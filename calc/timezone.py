# calc/timezone.py
"""
Timezone / DST resolution logic for JyotiSON.

Design goals:
- Pure calculation logic (no Streamlit dependency)
- Offline, deterministic
- Clear separation of auto vs manual resolution
- LLM-friendly result structure (meaning-preserving)

Dependencies:
- Python 3.11+
- timezonefinder
- zoneinfo (stdlib)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from timezonefinder import TimezoneFinder


# -------------------------------------------------
# Result type
# -------------------------------------------------
@dataclass(frozen=True)
class TimezoneResult:
    tz_name: str                 # IANA timezone name, e.g. "Asia/Tokyo"
    utc_offset_hours: float      # e.g. 9.0, -4.0
    is_dst: bool                 # daylight saving time at the given datetime
    source: str                  # "auto" | "manual"
    confidence: str              # "high" | "medium"


# -------------------------------------------------
# Core helpers
# -------------------------------------------------
_tf = TimezoneFinder(in_memory=True)


def detect_timezone_name(lat: float, lon: float) -> str | None:
    """
    Detect IANA timezone name from latitude / longitude.

    Returns:
        tz_name (str) or None if not found
    """
    try:
        return _tf.timezone_at(lat=lat, lng=lon)
    except Exception:
        return None


def compute_utc_offset(
    tz_name: str,
    local_dt: datetime,
) -> tuple[float, bool]:
    """
    Compute UTC offset and DST flag for a given timezone and local datetime.

    Args:
        tz_name: IANA timezone name
        local_dt: naive datetime interpreted as local time in tz_name

    Returns:
        (utc_offset_hours, is_dst)
    """
    tz = ZoneInfo(tz_name)

    # Interpret naive datetime as local time in the given timezone
    dt_local = local_dt.replace(tzinfo=tz)

    offset = dt_local.utcoffset()
    if offset is None:
        raise ValueError(f"Cannot compute UTC offset for timezone: {tz_name}")

    offset_hours = offset.total_seconds() / 3600.0

    dst = dt_local.dst()
    is_dst = bool(dst and dst.total_seconds() != 0)

    return offset_hours, is_dst


# -------------------------------------------------
# High-level resolver
# -------------------------------------------------
def resolve_timezone(
    *,
    lat: float,
    lon: float,
    local_dt: datetime,
    manual_utc_offset: float | None = None,
) -> TimezoneResult:
    """
    Resolve timezone / DST / UTC offset for birth data.

    Resolution rules:
    - If manual_utc_offset is provided:
        * timezone name is fixed to "Etc/GMT±X"
        * DST is always False
        * source = "manual"
    - Otherwise:
        * timezone is auto-detected from lat/lon
        * DST is computed from historical rules
        * source = "auto"

    Args:
        lat: latitude
        lon: longitude
        local_dt: naive datetime representing local birth time
        manual_utc_offset: optional manual UTC offset (hours)

    Returns:
        TimezoneResult
    """

    # -------------------------
    # Manual override
    # -------------------------
    if manual_utc_offset is not None:
        # Note: Etc/GMT signs are inverted by convention
        # UTC+9  -> Etc/GMT-9
        sign = "-" if manual_utc_offset > 0 else "+"
        hours = abs(int(manual_utc_offset))

        tz_name = f"Etc/GMT{sign}{hours}"

        return TimezoneResult(
            tz_name=tz_name,
            utc_offset_hours=float(manual_utc_offset),
            is_dst=False,
            source="manual",
            confidence="medium",
        )

    # -------------------------
    # Auto detection
    # -------------------------
    tz_name = detect_timezone_name(lat, lon)
    if tz_name is None:
        # Fallback: UTC (should be extremely rare)
        return TimezoneResult(
            tz_name="UTC",
            utc_offset_hours=0.0,
            is_dst=False,
            source="auto",
            confidence="low",
        )

    try:
        offset_hours, is_dst = compute_utc_offset(tz_name, local_dt)
    except Exception:
        # Safety fallback
        return TimezoneResult(
            tz_name=tz_name,
            utc_offset_hours=0.0,
            is_dst=False,
            source="auto",
            confidence="low",
        )

    return TimezoneResult(
        tz_name=tz_name,
        utc_offset_hours=offset_hours,
        is_dst=is_dst,
        source="auto",
        confidence="high",
    )