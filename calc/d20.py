# calc/d20.py
from typing import Dict
from .varga import vimsamsa_sign
from .base import SIGNS, house_from_signs

def build_d20(asc_long: float, planets_long: Dict[str, float], include_exaltation: bool = False) -> Dict:
    """
    Vimśāṁśa（D20）を構築。
    - asc_long: D1のASC黄経(0..360)（sidereal）
    - planets_long: 惑星→黄経(0..360)（sidereal）
    戻り値：
      {
        "Asc":{"sign": "Cn"},
        "planets": {
           "Su":{"sign":"Pi","house":9, "exalted":true?},
           ...
        }
      }
    """
    asc_sign = vimsamsa_sign(asc_long)
    asc_si = SIGNS.index(asc_sign)

    out_pl = {}
    for p, lon in planets_long.items():
        psign = vimsamsa_sign(lon)
        psi = SIGNS.index(psign)
        house = house_from_signs(asc_si, psi)
        entry = {"sign": psign, "house": house}
        out_pl[p] = entry

    return {"Asc": {"sign": asc_sign}, "planets": out_pl}
