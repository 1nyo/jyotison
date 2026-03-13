# calc/d60.py
from typing import Dict
from .varga import shastyamsa_sign
from .base import SIGNS, house_from_signs

def build_d60(asc_long: float, planets_long: Dict[str, float], include_exaltation: bool = False) -> Dict:
    """
    Ṣaṣṭiāṁśa（D60）を構築。JH “D-60 (Trd)” と整合。
    - asc_long: D1のASC黄経(0..360)
    - planets_long: 惑星→黄経(0..360)
    - include_exaltation: サイン基準の exalted を付ける場合 True（通常 False）
    """
    asc_sign = shastyamsa_sign(asc_long)  # ← mode を渡さない
    asc_si = SIGNS.index(asc_sign)

    out_pl = {}
    for p, lon in planets_long.items():
        psign = shastyamsa_sign(lon)      # ← mode を渡さない
        psi = SIGNS.index(psign)
        house = house_from_signs(asc_si, psi)
        entry = {"sign": psign, "house": house}
        # ★ exalted は出さない（dignity に集約）
        out_pl[p] = entry

    return {"Asc": {"sign": asc_sign}, "planets": out_pl}
