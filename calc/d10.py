# calc/d10.py

from typing import Dict
from .varga import dasamsa_sign
from .base import SIGNS, house_from_signs

def build_d10(asc_long: float, planets_long: Dict[str, float], include_exaltation: bool = False) -> Dict:
    """
    Daśāṁśa（D10）を構築。
    Parāśara式 D10（JH \"D-10 (Trd)\" と整合）を採用。
    D20/D60 同様、sign + house のみを出力。
    """
    # ★ ここが重要：ASC も D10 に変換する
    asc_sign = dasamsa_sign(asc_long)
    asc_si = SIGNS.index(asc_sign)

    out_pl: Dict[str, Dict] = {}
    for p, lon in planets_long.items():
        psign = dasamsa_sign(lon)   # 各惑星の D10 サイン
        psi = SIGNS.index(psign)
        house = house_from_signs(asc_si, psi)
        out_pl[p] = {"sign": psign, "house": house}

    return {"Asc": {"sign": asc_sign}, "planets": out_pl}