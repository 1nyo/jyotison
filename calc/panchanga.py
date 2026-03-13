# calc/panchanga.py
from typing import Tuple

TITHI_NAMES = [
    "Pratipada","Dvitiya","Tritiya","Chaturthi","Panchami","Shashthi","Saptami","Ashtami","Navami","Dashami",
    "Ekadashi","Dvadashi","Trayodasi","Chaturdasi","Purnima",
    "Pratipada","Dvitiya","Tritiya","Chaturthi","Panchami","Shashthi","Saptami","Ashtami","Navami","Dashami",
    "Ekadashi","Dvadashi","Trayodasi","Chaturdasi","Amavasya"
]

def tithi(mo_long: float, su_long: float) -> Tuple[str, str]:
    """
    %残なし（互換API）
    """
    diff = (mo_long - su_long) % 360.0
    idx = int(diff // 12.0) % 30
    paksha = "Shukla" if idx < 15 else "Krishna"
    return TITHI_NAMES[idx], paksha

def tithi_info(mo_long: float, su_long: float) -> Tuple[str, str, float]:
    """
    Tithi名, Paksha, percent_left(0..100) を返す。
    ※ JH に最も近いシンプル式：中間は float のまま、最後だけ round(…, 2)
    """
    diff = (mo_long - su_long) % 360.0       # 0..360
    idx = int(diff // 12.0) % 30             # 0..29
    offset_in_tithi = diff - (idx * 12.0)    # 0..12
    prog = offset_in_tithi / 12.0            # 0..1
    left = (1.0 - prog) * 100.0              # 0..100
    paksha = "Shukla" if idx < 15 else "Krishna"
    return TITHI_NAMES[idx], paksha, max(0.0, min(100.0, round(left, 2)))