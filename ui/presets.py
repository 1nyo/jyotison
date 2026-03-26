# ui/presets.py
"""
UI-layer preset management for JyotiSON.

Responsibilities:
- Own PRESET_KEYS and PRESETS definition (Basic/Standard/Advanced)
- Apply preset -> session_state
- Detect current state -> preset name or "Custom"
- Maintain UI state:
    - output_profile: actual profile name ("Basic"/"Standard"/"Advanced"/"Custom")
    - output_level: slider position ("Basic"/"Standard"/"Advanced")
    - is_custom: bool
    - preset_initialized: bool (first-run guard)

Design policy:
- This module touches only streamlit.session_state.
- No calc / input dependencies.
"""

from __future__ import annotations

from typing import Dict
import streamlit as st

# ----------------------------
# Keys used in session_state
# ----------------------------
K_OUTPUT_PROFILE = "output_profile"
K_OUTPUT_LEVEL = "output_level"
K_IS_CUSTOM = "is_custom"
K_PRESET_INITIALIZED = "preset_initialized"

# ----------------------------
# Preset-controlled keys
# ----------------------------
PRESET_KEYS = [
    # D1 output details
    "opt_nak_lord", "opt_aspects", "opt_conjunctions", "opt_speed_status",
    "opt_dig_bala", "opt_combust", "opt_planet_war", "opt_dignity_det",
    "opt_vargottama", "opt_gandanta",

    # Varga includes
    "include_d1", "include_d3", "include_d4", "include_d7", "include_d9",
    "include_d10", "include_d12", "include_d16", "include_d20",
    "include_d24", "include_d30", "include_d60",

    # Varga output options
    "varga_d9_degree", "varga_dignity",
]

# ----------------------------
# Preset profiles
# ----------------------------
PRESETS: Dict[str, Dict[str, bool]] = {
    "Basic": {
        # --- D1 Details ---
        "opt_nak_lord": False,
        "opt_aspects": False,
        "opt_conjunctions": False,
        "opt_speed_status": False,
        "opt_dig_bala": False,
        "opt_combust": True,         # policy: keep combust ON even in Basic
        "opt_planet_war": False,
        "opt_dignity_det": False,
        "opt_vargottama": False,
        "opt_gandanta": False,

        # --- Varga ---
        "include_d1": True,
        "include_d9": True,
        "include_d3": False,
        "include_d4": False,
        "include_d7": False,
        "include_d10": False,
        "include_d12": False,
        "include_d16": False,
        "include_d20": False,
        "include_d24": False,
        "include_d30": False,
        "include_d60": False,

        # --- Varga Output ---
        "varga_d9_degree": False,
        "varga_dignity": False,
    },

    "Standard": {
        # --- D1 Details ---
        "opt_nak_lord": True,
        "opt_aspects": True,
        "opt_conjunctions": True,
        "opt_speed_status": False,
        "opt_dig_bala": False,
        "opt_combust": True,
        "opt_planet_war": False,
        "opt_dignity_det": True,
        "opt_vargottama": True,
        "opt_gandanta": True,

        # --- Varga ---
        "include_d1": True,
        "include_d9": True,
        "include_d10": True,
        "include_d20": True,
        "include_d60": True,
        "include_d3": False,
        "include_d4": False,
        "include_d7": False,
        "include_d12": False,
        "include_d16": False,
        "include_d24": False,
        "include_d30": False,

        # --- Varga Output ---
        "varga_d9_degree": True,
        "varga_dignity": True,
    },

    "Advanced": {
        # everything ON
        **{k: True for k in PRESET_KEYS},
    },
}

VALID_LEVELS = ("Basic", "Standard", "Advanced")


# ----------------------------
# Core helpers
# ----------------------------
def apply_preset_to_session(preset_name: str) -> None:
    """
    Apply a preset profile values to session_state.
    No-op if unknown preset.
    """
    profile = PRESETS.get(preset_name)
    if not profile:
        return
    for key, val in profile.items():
        st.session_state[key] = bool(val)


def detect_preset_from_state() -> str:
    """
    Returns "Basic"/"Standard"/"Advanced" if exactly matches.
    Otherwise returns "Custom".
    """
    current = {k: bool(st.session_state.get(k, False)) for k in PRESET_KEYS}
    for name in VALID_LEVELS:
        if current == PRESETS[name]:
            return name
    return "Custom"


def ensure_preset_state(default_profile: str = "Standard") -> None:
    """
    Initialize preset-related session_state.
    Applies default preset only once (first run), matching current behavior.
    """
    if default_profile not in VALID_LEVELS:
        default_profile = "Standard"

    st.session_state.setdefault(K_OUTPUT_PROFILE, default_profile)
    st.session_state.setdefault(K_OUTPUT_LEVEL, st.session_state[K_OUTPUT_PROFILE])
    st.session_state.setdefault(K_IS_CUSTOM, False)

    # First run: apply default preset
    if K_PRESET_INITIALIZED not in st.session_state:
        apply_preset_to_session(st.session_state[K_OUTPUT_PROFILE])
        st.session_state[K_PRESET_INITIALIZED] = True


# ----------------------------
# Streamlit callbacks (no-arg)
# ----------------------------
def on_preset_slider_change() -> None:
    """
    Called when the preset slider changes.
    - Apply selected preset (Basic/Standard/Advanced)
    - Exit Custom mode
    """
    new_level = st.session_state.get(K_OUTPUT_LEVEL, "Standard")
    if new_level not in VALID_LEVELS:
        new_level = "Standard"

    apply_preset_to_session(new_level)
    st.session_state[K_OUTPUT_PROFILE] = new_level
    st.session_state[K_IS_CUSTOM] = False


def on_manual_option_changed() -> None:
    """
    Called when any option checkbox changes manually.
    - If matches a preset exactly -> sync profile and slider; Custom off
    - Else -> enter Custom mode
    """
    detected = detect_preset_from_state()

    if detected in VALID_LEVELS:
        st.session_state[K_OUTPUT_PROFILE] = detected
        st.session_state[K_OUTPUT_LEVEL] = detected
        st.session_state[K_IS_CUSTOM] = False
    else:
        st.session_state[K_OUTPUT_PROFILE] = "Custom"
        st.session_state[K_IS_CUSTOM] = True


def current_profile_for_desc() -> str:
    """
    Helper for UI: which profile label to show description for.
    """
    if st.session_state.get(K_IS_CUSTOM, False):
        return "Custom"
    return st.session_state.get(K_OUTPUT_PROFILE, st.session_state.get(K_OUTPUT_LEVEL, "Standard"))