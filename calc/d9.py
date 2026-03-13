# calc/d9.py
from typing import Dict
from .varga import d9_sign_and_degree
from .base import SIGNS, house_from_signs

def build_d9(asc_long: float, planets_long: Dict[str, float]) -> Dict:
    """
    asc_long: D1 の ASC 絶対黄経（0..360）
    planets_long: 惑星 → 絶対黄経（0..360）
    戻り値:
      {
        "Asc": {"sign":..., "degree":...},                       # D9空間
        "planets": {"Su":{"sign":..,"degree":..,"house":..}, ...} # D9空間
      }
    """
    asc_sign, asc_deg_d9 = d9_sign_and_degree(asc_long)
    asc_si = SIGNS.index(asc_sign)

    pls = {}
    for p, lon in planets_long.items():
        psign, pdeg_d9 = d9_sign_and_degree(lon)
        psi = SIGNS.index(psign)
        house = house_from_signs(asc_si, psi)  # D9 Asc sign を 1室とする Whole Sign
        pls[p] = {"sign": psign, "degree": pdeg_d9, "house": house}

    return {"Asc": {"sign": asc_sign, "degree": asc_deg_d9}, "planets": pls}
