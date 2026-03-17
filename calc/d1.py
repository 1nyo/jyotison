# calc/d1.py
from typing import Dict
from .base import house_from_signs, SIGNS
from .ephemeris import pack_sidereal_point
from .speed import flags as speed_flags, classify_speed

def build_d1(
    asc_long: float,
    planets: Dict[str, Dict],
) -> Dict:
    """
    D1（Rāśi）を構築。

    方針:
    ------------------------------------------------------------
    - retrograde は speed とは独立・常時出力（Sun は除外、Ra は抑止）。
    - speed は {value, status} を常に計算して出力に含める。
      （出力 ON/OFF は streamlit_app.py の apply_output_options で削る）
    - status は 'station' / 'very_fast' / 'fast' / 'very_slow' / 'normal'
    - Ke は速度関連すべて抑止
    ------------------------------------------------------------
    """
    asc = pack_sidereal_point(asc_long)
    asc_sign = asc["sign"]
    asc_si = SIGNS.index(asc_sign)

    out_planets = {}

    for p, pp in planets.items():
        # --- sign ---
        raw_sign = pp.get("sign")
        sign = raw_sign if isinstance(raw_sign, str) and raw_sign in SIGNS else asc_sign

        # --- degree ---
        raw_degree = pp.get("degree")
        degree = float(raw_degree) if isinstance(raw_degree, (int, float)) else raw_degree

        # --- nakshatra ---
        nak = pp.get("nakshatra")

        # --- speed value ---
        raw_speed = pp.get("speed", 0.0)
        try:
            spd = float(raw_speed)
        except Exception:
            spd = 0.0

        # --- house (Whole Sign) ---
        try:
            si = SIGNS.index(sign)
        except ValueError:
            si = asc_si
        house = house_from_signs(asc_si, si)

        # --------------------------
        # 出力エントリ
        # --------------------------
        entry = {
            "sign": sign,
            "degree": degree,
            "house": house,
            "nakshatra": nak,
        }

        # --------------------------
        # retrograde / speed  (Ke除外)
        # --------------------------
        if p != "Ke":
            fl = speed_flags(p, spd)

            # retrograde は speed とは独立
            if fl.get("retrograde") and p != "Ra":
                entry["retrograde"] = True

            # speed は常に full 出力
            status = classify_speed(p, spd)
            entry["speed"] = {
                "value": spd,
                "status": status
            }

        # p == "Ke": speed は一切付けない

        out_planets[p] = entry

    return {"Asc": asc, "planets": out_planets}
