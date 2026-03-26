# ui/geo_timezone.py
"""
UI-layer state transitions for:
- geo_paste (Google Maps coords/share link)
- lat/lon manual edits
- timezone auto/manual mode flags (tz_mode, tz_dirty)
- rerun-safe geo success/error message state

Design policy:
- This module owns ONLY Streamlit session state transitions.
- Parsing logic lives in input/location.py (passed in as parse_func).
- Timezone calculation lives in calc/timezone.py (called in streamlit_app.py).
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, TypedDict, Literal
import streamlit as st


# ----------------------------
# Types
# ----------------------------
GeoMsgKind = Literal["none", "ok", "error"]

class GeoMsgState(TypedDict, total=False):
    kind: GeoMsgKind
    lat: float
    lon: float
    confidence: str  # "high" | "low" etc.
    # You can extend later if needed (e.g., raw text)


# ----------------------------
# Session-state keys (single source of truth)
# ----------------------------
K_PREV_PASTE = "_prev_geo_paste"
K_GEO_SUCCESS = "_geo_success"         # {"lat","lon","confidence"} or None
K_GEO_MSG_STATE = "_geo_msg_state"     # {"kind":..., ...}
K_GEO_CONF = "geo_confidence"

K_TZ_MODE = "tz_mode"                 # "auto" | "manual"
K_TZ_DIRTY = "tz_dirty"               # bool
K_GEO_PASTE = "geo_paste"             # text input key


# ----------------------------
# Init
# ----------------------------
def ensure_geo_tz_state() -> None:
    """
    Safe defaults. Call once early (before widgets) or anytime.
    """
    st.session_state.setdefault(K_PREV_PASTE, "")
    st.session_state.setdefault(K_GEO_SUCCESS, None)
    st.session_state.setdefault(K_GEO_MSG_STATE, {"kind": "none"})
    st.session_state.setdefault(K_GEO_CONF, None)

    st.session_state.setdefault(K_TZ_MODE, "auto")
    st.session_state.setdefault(K_TZ_DIRTY, True)


# ----------------------------
# TZ flags helpers
# ----------------------------
def mark_tz_dirty() -> None:
    """
    Any relevant input changed -> go back to auto detection.
    """
    st.session_state[K_TZ_DIRTY] = True
    st.session_state[K_TZ_MODE] = "auto"


def on_tz_manual_change() -> None:
    """
    User touched UTC offset manually.
    Keep geo success message; do NOT trigger auto.
    """
    st.session_state[K_TZ_MODE] = "manual"
    st.session_state[K_TZ_DIRTY] = False


# ----------------------------
# Geo paste / lat-lon interactions
# ----------------------------
def clear_geo_paste() -> None:
    """
    Clear pasted location and related message state.
    This is explicit user action (X button).
    """
    st.session_state[K_GEO_PASTE] = ""
    st.session_state[K_PREV_PASTE] = ""
    st.session_state[K_GEO_SUCCESS] = None
    st.session_state[K_GEO_MSG_STATE] = {"kind": "none"}
    st.session_state[K_GEO_CONF] = None

    # Keep your original intention: clearing paste does NOT automatically recalc tz
    st.session_state[K_TZ_DIRTY] = False


def on_latlon_manual_change() -> None:
    """
    If user manually edits lat/lon:
    - pasted mode becomes invalid -> clear geo_paste and message
    - timezone should be recalculated in auto mode
    """
    st.session_state[K_GEO_PASTE] = ""
    st.session_state[K_PREV_PASTE] = ""
    st.session_state[K_GEO_SUCCESS] = None
    st.session_state[K_GEO_MSG_STATE] = {"kind": "none"}
    st.session_state[K_GEO_CONF] = None

    mark_tz_dirty()


# ----------------------------
# Core: handle geo_paste processing (state-only)
# ----------------------------
def handle_geo_paste(
    geo_paste: str,
    parse_func: Callable[[str], Any],
) -> GeoMsgState:
    """
    Process geo_paste ONLY when it changed.
    Update session_state lat/lon, geo_confidence, tz flags, and message state.

    Returns current message state (rerun-safe).
    """
    ensure_geo_tz_state()

    prev = st.session_state.get(K_PREV_PASTE, "")
    changed = (geo_paste != prev)
    st.session_state[K_PREV_PASTE] = geo_paste

    # If empty -> clear message & success
    if not geo_paste:
        st.session_state[K_GEO_SUCCESS] = None
        st.session_state[K_GEO_MSG_STATE] = {"kind": "none"}
        st.session_state[K_GEO_CONF] = None
        return st.session_state[K_GEO_MSG_STATE]

    # If not changed -> keep existing state (important for reruns like tz manual change)
    if not changed:
        return st.session_state.get(K_GEO_MSG_STATE, {"kind": "none"})

    # Changed -> parse new text
    res = parse_func(geo_paste)

    if not res:
        st.session_state[K_GEO_SUCCESS] = None
        st.session_state[K_GEO_CONF] = None
        st.session_state[K_GEO_MSG_STATE] = {"kind": "error"}
        return st.session_state[K_GEO_MSG_STATE]

    # Success
    pasted_lat, pasted_lon = float(res.lat), float(res.lon)
    confidence = getattr(res, "confidence", None) or "high"

    # Update coordinates before widgets are created
    st.session_state["lat"] = pasted_lat
    st.session_state["lon"] = pasted_lon

    # Switching coordinates should trigger timezone auto detection
    mark_tz_dirty()

    st.session_state[K_GEO_SUCCESS] = {
        "lat": pasted_lat,
        "lon": pasted_lon,
        "confidence": confidence,
    }
    st.session_state[K_GEO_CONF] = confidence

    st.session_state[K_GEO_MSG_STATE] = {
        "kind": "ok",
        "lat": pasted_lat,
        "lon": pasted_lon,
        "confidence": confidence,
    }
    return st.session_state[K_GEO_MSG_STATE]


# ----------------------------
# Renderer helper (optional but convenient)
# ----------------------------
def render_geo_message(
    placeholder: Any,
    t: Callable[[str], str],
    geo_paste: str,
) -> None:
    """
    Rerun-safe rendering for geo messages.
    - Shows success while geo_paste exists and last state is ok
    - Shows error while geo_paste exists and last state is error
    - Clears when geo_paste empty
    """
    ensure_geo_tz_state()
    state: GeoMsgState = st.session_state.get(K_GEO_MSG_STATE, {"kind": "none"})

    if not geo_paste:
        placeholder.empty()
        return

    kind = state.get("kind", "none")

    if kind == "error":
        placeholder.error(t("geo_error"))
        return

    if kind == "ok":
        lat = state.get("lat")
        lon = state.get("lon")
        placeholder.success(
            t("geo_success").format(default_lat=lat, default_lon=lon)
        )
        if state.get("confidence") == "low":
            placeholder.warning(t("geo_notice_low_conf"))
        return

    # kind == "none" (rare): keep empty
    placeholder.empty()
    