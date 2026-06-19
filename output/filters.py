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
from typing import Dict, List, Tuple
import copy

# ---------------------------------------------------------------------------
# 定義：opt_key → 削除フィールド のマッピング
# ---------------------------------------------------------------------------

# D1 derived セクションに適用するフィルター
_DERIVED_FILTERS: List[Tuple[str, str]] = [
    ("dig_bala",       "dig_bala"),
    ("vargottama",     "vargottama"),
    ("gandanta",       "gandanta"),
    ("aspects",        "aspects_to_sign"),
    ("conjunctions",   "occupancy_in_sign"),
    ("combust",        "combust"),
    ("planet_war",     "planetary_war"),
]

# dignity フィルターの許容値（dignity_detail OFF時のみ保持）
_DIGNITY_KEEP = {"exalted", "debilitated", "moolatrikona", "owned"}

def _apply_planet_filters(rec: Dict, opt: Dict, planet_key: str) -> None:
    """
    単一惑星レコードから不要フィールドを削除。
    """

    is_moon = planet_key == "Mo"

    nak = rec.get("nakshatra")

    if isinstance(nak, dict):

        # 月は常に保持
        if not is_moon:
            if not opt.get("nakshatra", False):
                rec.pop("nakshatra", None)

    # -------------------------------
    # 他フィールド（そのまま）
    # -------------------------------
    for opt_key, field in (
        ("aspects",      "aspects_to_sign"),
        ("conjunctions", "occupancy_in_sign"),
        ("combust",      "combust"),
        ("planet_war",   "planet_war"),
        ("dig_bala",     "dig_bala"),
        ("vargottama",   "vargottama"),
        ("gandanta",     "gandanta"),
    ):
        if not opt.get(opt_key, False):
            rec.pop(field, None)

    # dignity
    if not opt.get("dignity_detail", False):
        dignity = rec.get("dignity")
        if isinstance(dignity, str) and dignity not in _DIGNITY_KEEP:
            rec.pop("dignity", None)

    # speed
    speed = rec.get("speed")
    if isinstance(speed, dict):

        if not opt.get("speed_status", False):
            rec.pop("speed", None)
        else:
            if speed.get("status") == "normal":
                rec.pop("speed", None)

    
    # -------------------------------
    # speed（normal は出力しない）
    # -------------------------------
    speed = rec.get("speed")
    if isinstance(speed, dict):

        # speed 全体 OFF
        if not opt.get("speed_status", False):
            rec.pop("speed", None)

        else:
            # status == normal は出さない
            if speed.get("status") == "normal":
                rec.pop("speed", None)


def _apply_derived_filters(derived: Dict, opt: Dict) -> None:
    """
    D1 derived セクションから不要フィールドを削除。
    """
    for opt_key, field in _DERIVED_FILTERS:
        if not opt.get(opt_key, False):
            derived.pop(field, None)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

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
    # D1 (Asc + planets + derived)
    # -------------------------------
    d1 = charts.get("D1")
    if isinstance(d1, dict):
        # Asc
        asc = d1.get("Asc")
        if isinstance(asc, dict):
            # AscのNakshatraは常に保持（フィルタリングしない）
            pass
        #   nakshatra を保持しない場合は次のコメントを外す
        #   if not opt.get("nakshatra", False):
        #       asc.pop("nakshatra", None)

        # planets
        if isinstance(d1.get("planets"), dict):
            for p_key, rec in d1["planets"].items():
                if isinstance(rec, dict):
                    _apply_planet_filters(rec, opt, p_key)

        # derived
        derived = d1.get("derived")
        if isinstance(derived, dict):
            _apply_derived_filters(derived, opt)

    # -------------------------------
    # D9
    # -------------------------------
    d9 = charts.get("D9")
    if isinstance(d9, dict):
        if not opt.get("varga_d9_degree", False):
            if isinstance(d9.get("Asc"), dict):
                d9["Asc"].pop("degree", None)
            if isinstance(d9.get("planets"), dict):
                for rec in d9["planets"].values():
                    if isinstance(rec, dict):
                        rec.pop("degree", None)

    # -------------------------------
    # D3 ~ D60
    # -------------------------------
    for cname, chart in charts.items():
        if cname in ("D1", "D9") or not isinstance(chart, dict):
            continue

        # --- degree ---
        if not opt.get("varga_degree", False):
            if isinstance(chart.get("Asc"), dict):
                chart["Asc"].pop("degree", None)
            if isinstance(chart.get("planets"), dict):
                for rec in chart["planets"].values():
                    if isinstance(rec, dict):
                        rec.pop("degree", None)

        # --- dignity ---
        if not opt.get("varga_dignity", False):
            if isinstance(chart.get("planets"), dict):
                for rec in chart["planets"].values():
                    if isinstance(rec, dict):
                        rec.pop("dignity", None)

    return charts