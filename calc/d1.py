# calc/d1.py
from typing import Dict
from .base import house_from_signs, is_exalted, SIGNS
from .ephemeris import pack_sidereal_point
from .speed import flags as speed_flags, is_normal_speed

def build_d1(
    asc_long: float,
    planets: Dict[str, Dict],
    include_speed_flags: bool = True,
) -> Dict:
    """
    D1（Rāśi）を構築。
    - retrograde は speed とは独立の boolean として常時出力（Sunは除外、Keは速度関連すべて抑止）。
    - speed は {value, status} 形式。include_speed_flags=True の場合のみ出力し、
      通常は normal を省略（normal時は出さない）。status は retrograde を重複表示しない方針。
    """
    asc = pack_sidereal_point(asc_long)
    asc_sign = asc["sign"]
    asc_si = SIGNS.index(asc_sign)

    out_planets = {}

    for p, pp in planets.items():
        # --- 安全な取り出し（型ガード） ---
        raw_sign = pp.get("sign")
        sign: str = raw_sign if isinstance(raw_sign, str) and raw_sign in SIGNS else asc_sign  # fallback to Asc sign

        # degree は 0.00..29.99（float）想定。なければ None のままでも良いが、数値なら float 化
        raw_degree = pp.get("degree")
        degree = float(raw_degree) if isinstance(raw_degree, (int, float)) else raw_degree  # そのまま None 可

        # nakshatra は {"name": str, "pada": int} を想定。pack_sidereal_point 準拠。
        nak = pp.get("nakshatra")
        if not (isinstance(nak, dict) and "name" in nak and "pada" in nak):
            # 形式不正の場合でも落ちない（出力は現状のまま or 必要なら None にする）
            # ここではそのまま nak を通す
            pass

        # speed（deg/day）。無い場合は 0.0
        raw_speed = pp.get("speed", 0.0)
        try:
            spd = float(raw_speed)
        except Exception:
            spd = 0.0

        # --- house 計算（Whole Sign） ---
        try:
            si = SIGNS.index(sign)                 # sign は str で保証済
        except ValueError:
            si = asc_si                            # 念のためフォールバック
        house = house_from_signs(asc_si, si)       # 1..12

        # ---- 出力エントリ（順序保持：nakshatra の直後に retrograde）----
        entry = {
            "sign": sign,
            "degree": degree,
            "house": house,
            "nakshatra": nak,
        }

        # --- 速度系（Sun常順行, Keは全抑止, Raはretrograde抑止） ---
        if p != "Ke":
            fl = speed_flags(p, spd)

            # retrograde は speed とは独立・常時出力。ただし Ra は抑止
            if fl.get("retrograde") and p != "Ra":
                entry["retrograde"] = True

            # 速度ラベル・数値は include_speed_flags=True のときのみ
            if include_speed_flags:
                status = None
                for key in ("station", "very_fast", "fast", "very_slow"):
                    if fl.get(key):
                        status = key
                        break
                # normal 以外のときだけ speed を出す（従来合意）
                if status or (not is_normal_speed(p, spd)):
                    entry["speed"] = {
                        "value": spd,
                        "status": status if status else "normal"
                    }
        # p == "Ke": 速度関連（retrograde含む）を一切出さない

        out_planets[p] = entry

    out = {"Asc": asc, "planets": out_planets}

    return out
