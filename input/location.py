# input/location.py
"""
Location input parser for JyotiSON.

Goals:
- Parse pasted strings into (lat, lon) with confidence and source.
- Accept:
  • Plain "lat, lon" text
  • Google Maps long URLs with @lat,lon or !3d!4d
  • Google Maps official URLs (?q=lat,lon etc.)
  • Google Maps short URLs (maps.app.goo.gl only)
- No Streamlit dependency (caller may wrap with st.cache_data if desired).
- SSRF-safe: restrict outbound fetch targets to:
  • maps.app.goo.gl (short URL resolution)
  • www.google.com / google.com (maps pages + preview)
"""

from __future__ import annotations

import html as _html
import re
from dataclasses import dataclass
from urllib.parse import urlparse, parse_qs, urljoin, unquote
from urllib.request import Request, urlopen


# -----------------------------
# Result type
# -----------------------------
@dataclass(frozen=True)
class LocationResult:
    lat: float
    lon: float
    confidence: str  # "high" | "medium" | "low"
    source: str      # for debugging/telemetry (not necessarily shown to users)


# -----------------------------
# Constants / regex
# -----------------------------
# URL extraction: supports "facility name + URL" paste. (Not intended for concatenated URLs.)
_URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)

# Coordinate extraction patterns
_RE_3D4D = re.compile(r"!3d(-?\d+(?:\.\d+)?)!4d(-?\d+(?:\.\d+)?)")
_RE_AT = re.compile(r"@(-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)")
_RE_CENTER = re.compile(r"center=([-0-9\.]+)(?:%2C|,)([-0-9\.]+)")
_RE_2D3D = re.compile(r"!2d(-?\d+(?:\.\d+)?)!3d(-?\d+(?:\.\d+)?)")  # noisy, low confidence

# Plain text coordinate pair only (prevents digits in URLs being misread)
_RE_PLAIN_PAIR = re.compile(
    r"(-?\d{1,2}(?:\.\d+)?)\s*,\s*(-?\d{1,3}(?:\.\d+)?)"
    r"|(-?\d{1,2}(?:\.\d+)?)\s+(-?\d{1,3}(?:\.\d+)?)"
)

_ALLOWED_SHORT_HOST = "maps.app.goo.gl"
_ALLOWED_GOOGLE_HOSTS = {"www.google.com", "google.com"}


# -----------------------------
# Public API
# -----------------------------
def parse_location_input(text: str) -> LocationResult | None:
    """
    Main entrypoint.
    Returns LocationResult(lat, lon, confidence, source) or None.

    confidence:
      - high: true place coords (!3d!4d) or plain coordinate pair
      - medium: map center (@lat,lon) or query params / center=
      - low: noisy fallback from pb (!2d lon !3d lat)
    """
    if not text:
        return None

    # 1) URL path (if present)
    url = _first_url(text)
    if url:
        # 1-A) Directly parse URL string without network
        res = _extract_from_url_text(url)
        if res:
            return res

        # 1-B) Short URL resolution (maps.app.goo.gl only)
        if urlparse(url).netloc.lower() == _ALLOWED_SHORT_HOST:
            final_url = resolve_maps_app_short_url(url)
            if final_url:
                # Sometimes coords appear in final_url itself
                res2 = _extract_from_url_text(final_url)
                if res2:
                    return res2

                # Fetch the (B) page once
                html_text = fetch_google_text_limited(final_url)
                if html_text:
                    # Try extracting from that HTML blob
                    res3 = _extract_from_blob(html_text)
                    if res3:
                        return res3

                    # Preview preload fallback (often the key for Android share links)
                    preview_url = extract_preview_url_from_html(html_text, final_url)
                    if preview_url:
                        preview_text = fetch_google_text_limited(preview_url)
                        if preview_text:
                            res4 = _extract_from_blob(preview_text)
                            if res4:
                                return res4

    # 2) Plain text fallback: remove URLs then parse real coordinate pair
    text_wo_urls = _URL_RE.sub(" ", text)
    return _extract_from_plain_text(text_wo_urls)


# -----------------------------
# Network helpers (no caching here)
# Caller should wrap with st.cache_data if desired
# -----------------------------
def resolve_maps_app_short_url(url: str) -> str | None:
    """
    Resolve maps.app.goo.gl short URL to the next URL.
    Returns response.geturl() (post-redirect URL) or None.

    SECURITY: only allows maps.app.goo.gl
    """
    try:
        parsed = urlparse(url)
        if parsed.netloc.lower() != _ALLOWED_SHORT_HOST:
            return None

        req = Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urlopen(req, timeout=5) as resp:
            return resp.geturl()
    except Exception:
        return None


def fetch_google_text_limited(url: str, max_bytes: int = 2_000_000) -> str:
    """
    Fetch text from google.com only (SSRF-safe), up to max_bytes.
    Returns decoded text, or "" on failure.
    """
    try:
        host = urlparse(url).netloc.lower()
        if host not in _ALLOWED_GOOGLE_HOSTS:
            return ""

        req = Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,ja;q=0.8",
            },
        )
        with urlopen(req, timeout=7) as resp:
            data = resp.read(max_bytes)
            return data.decode("utf-8", errors="ignore")
    except Exception:
        return ""


# -----------------------------
# Extraction helpers
# -----------------------------
def _first_url(text: str) -> str | None:
    m = _URL_RE.search(text or "")
    return m.group(0) if m else None


def _extract_from_url_text(url: str) -> LocationResult | None:
    """
    Parse coordinates from URL string only (no network).
    Priority:
      1) !3dLAT!4dLON  -> high
      2) @LAT,LON      -> medium
      3) q/query/center=LAT,LON -> medium
    """
    if not url:
        return None

    # 1) true place coords
    m = _RE_3D4D.search(url)
    if m:
        lat, lon = float(m.group(1)), float(m.group(2))
        if _valid_latlon(lat, lon):
            return LocationResult(lat, lon, "high", "url_3d4d")

    # 2) map center
    m = _RE_AT.search(url)
    if m:
        lat, lon = float(m.group(1)), float(m.group(2))
        if _valid_latlon(lat, lon):
            return LocationResult(lat, lon, "medium", "url_at")

    # 3) official params
    try:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        for key in ("q", "query", "center"):
            if key in qs and qs[key]:
                m2 = re.search(r"(-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)", qs[key][0])
                if m2:
                    lat, lon = float(m2.group(1)), float(m2.group(2))
                    if _valid_latlon(lat, lon):
                        return LocationResult(lat, lon, "medium", f"url_param_{key}")
    except Exception:
        pass

    return None


def _extract_from_plain_text(text: str) -> LocationResult | None:
    """
    Extract from plain text coordinate pair.
    High confidence (user explicitly pasted coordinates).
    """
    if not text:
        return None

    m = _RE_PLAIN_PAIR.search(text)
    if not m:
        return None

    if m.group(1) and m.group(2):
        lat, lon = float(m.group(1)), float(m.group(2))
    else:
        lat, lon = float(m.group(3)), float(m.group(4))

    if _valid_latlon(lat, lon):
        return LocationResult(lat, lon, "high", "plain_text")

    return None


def extract_preview_url_from_html(html_text: str, base_url: str) -> str | None:
    """
    Find preload URL like:
      href="/maps/preview/place?...&pb=..."
    and return absolute URL.
    """
    if not html_text:
        return None

    h = _html.unescape(html_text)
    m = re.search(r'href="(/maps/preview/place\?[^"]+)"', h)
    if not m:
        return None

    return urljoin(base_url, m.group(1))


def _extract_from_blob(text: str) -> LocationResult | None:
    """
    Extract coords from HTML / preview response blobs (decoded).
    Priority:
      1) !3dLAT!4dLON  -> high
      2) @LAT,LON      -> medium
      3) center=LAT,LON -> medium
      4) !2dLON!3dLAT  -> low (noisy last resort)
    """
    if not text:
        return None

    t = _html.unescape(text)
    t = unquote(t)

    m = _RE_3D4D.search(t)
    if m:
        lat, lon = float(m.group(1)), float(m.group(2))
        if _valid_latlon(lat, lon):
            return LocationResult(lat, lon, "high", "blob_3d4d")

    m = _RE_AT.search(t)
    if m:
        lat, lon = float(m.group(1)), float(m.group(2))
        if _valid_latlon(lat, lon):
            return LocationResult(lat, lon, "medium", "blob_at")

    m = _RE_CENTER.search(t)
    if m:
        lat, lon = float(m.group(1)), float(m.group(2))
        if _valid_latlon(lat, lon):
            return LocationResult(lat, lon, "medium", "blob_center")

    # Noisy fallback (keep, but mark as low confidence)
    m = _RE_2D3D.search(t)
    if m:
        lon, lat = float(m.group(1)), float(m.group(2))
        if _valid_latlon(lat, lon):
            return LocationResult(lat, lon, "low", "blob_2d3d_noisy")

    return None


def _valid_latlon(lat: float, lon: float) -> bool:
    return (-90.0 <= lat <= 90.0) and (-180.0 <= lon <= 180.0)
