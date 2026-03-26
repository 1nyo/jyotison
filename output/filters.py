# output/filters.py
"""
Output filtering utilities for JyotiSON.

Responsibilities:
- Apply output option flags to charts dict
- Remove optional fields based on user-selected options
- Preserve schema shape and LLM-meaningful fields

Design policy:
- Pure function: no Streamlit, no session_state
- No calculation logic (already computed values only)
- Safe to unit-test
"""

from __future__ import annotations
from typing import Dict
import copy


def apply_output_options(charts: Dict, opt: Dict) -> Dict:
    """
    Apply output masking options to charts.

    Parameters
    ----------
    charts : dict
        charts dict after full calculation (D1, D9, D3...).
    opt : dict
        output option flags (bool).

    Returns
    -------
    dict
        filtered charts dict (deep-copied).
    """
    charts = copy.deepcopy(charts)

    # -------------------------------
    # D1 (planets + derived)
    # -------------------------------
    d1 = charts.get("D1")
    if isinstance(d1, dict):

        # ----- Asc -----
        asc = d1.get("Asc")
        if isinstance(asc, dict):
            if not opt.get("nakshatra_lord", False):
                if isinstance(asc.get("nakshatra"), dict):
                    asc["nakshatra"].pop("lord", None)

        # ----- planets -----
        planets = d1.get("planets")
        if isinstance(planets, dict):
            for _, rec in planets.items():
                if not isinstance(rec, dict):
                    continue

                # nakshatra lord
                if not opt.get("nakshatra_lord", False):
                    if isinstance(rec.get("nakshatra"), dict):
                        rec["nakshatra"].pop("lord", None)

                # aspects
                if not opt.get("aspects", False):
                    rec.pop("aspects_to_sign", None)

                # conjunctions
                if not opt.get("conjunctions", False):
                    rec.pop("occupancy_in_sign", None)

                # combust
                if not opt.get("combust", False):
                    rec.pop("combust", None)

                # planetary war
                if not opt.get("planet_war", False):
                    rec.pop("planet_war", None)

                # dignity detail
                if not opt.get("dignity_detail", False):
                    dignity = rec.get("dignity")
                    if isinstance(dignity, str):
                        KEEP = {"exalted", "debilitated", "moolatrikona", "owned"}
                        if dignity not in KEEP:
                            rec.pop("dignity", None)

                # dig bala
                if not opt.get("dig_bala", False):
                    rec.pop("dig_bala", None)

                # vargottama
                if not opt.get("vargottama", False):
                    rec.pop("vargottama", None)

                # gandanta
                if not opt.get("gandanta", False):
                    rec.pop("gandanta", None)

                # speed status
                if not opt.get("speed_status", False):
                    rec.pop("speed", None)

        # ----- derived -----
        derived = d1.get("derived")
        if isinstance(derived, dict):

            if not opt.get("dig_bala", False):
                derived.pop("dig_bala", None)

            if not opt.get("vargottama", False):
                derived.pop("vargottama", None)

            if not opt.get("gandanta", False):
                derived.pop("gandanta", None)

            if not opt.get("aspects", False):
                derived.pop("aspects_to_sign", None)

            if not opt.get("conjunctions", False):
                derived.pop("occupancy_in_sign", None)

            if not opt.get("combust", False):
                derived.pop("combust", None)

            if not opt.get("planet_war", False):
                derived.pop("planetary_war", None)

            # lordship_to_houses is always kept (LLM-meaningful core)

    # -------------------------------
    # D9
    # -------------------------------
    d9 = charts.get("D9")
    if isinstance(d9, dict):

        # Asc
        if isinstance(d9.get("Asc"), dict):
            if not opt.get("varga_d9_degree", False):
                d9["Asc"].pop("degree", None)

        # planets
        if isinstance(d9.get("planets"), dict):
            if not opt.get("varga_d9_degree", False):
                for rec in d9["planets"].values():
                    if isinstance(rec, dict):
                        rec.pop("degree", None)

    # -------------------------------
    # D3 ~ D60
    # -------------------------------
    for cname, chart in charts.items():
        if cname in ("D1", "D9"):
            continue
        if not isinstance(chart, dict):
            continue

        if not opt.get("varga_dignity", False):
            if isinstance(chart.get("planets"), dict):
                for rec in chart["planets"].values():
                    if isinstance(rec, dict):
                        rec.pop("dignity", None)

    return charts