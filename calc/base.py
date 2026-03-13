# calc/base.py
from dataclasses import dataclass
from typing import Dict, Tuple, List

SIGNS: List[str] = ["Ar","Ta","Ge","Cn","Le","Vi","Li","Sc","Sg","Cp","Aq","Pi"]
PLANETS: List[str] = ["Su","Mo","Ma","Me","Ju","Ve","Sa","Ra","Ke"]

# Exaltation（サイン単位で簡略化: 精神解析用途でブールのみ出力）
EXALTATION_SIGN: Dict[str, str] = {
    "Su": "Ar", "Mo": "Ta", "Ma": "Cp", "Me": "Vi",
    "Ju": "Cn", "Ve": "Pi", "Sa": "Li", "Ra": "Ta", "Ke": "Sc"
}

# サイン→支配星（D1 Lords）
SIGN_LORD: Dict[str, str] = {
    "Ar": "Ma", "Ta": "Ve", "Ge": "Me", "Cn": "Mo", "Le": "Su", "Vi": "Me",
    "Li": "Ve", "Sc": "Ma", "Sg": "Ju", "Cp": "Sa", "Aq": "Sa", "Pi": "Ju",
}

# Nakshatra (abbr, name)
NAKSHATRA: List[Tuple[str, str]] = [
    ("Asw", "Ashwini"), ("Bha", "Bharani"), ("Kri", "Krittika"), ("Roh","Rohini"),
    ("Mri","Mrigashira"), ("Ard","Ardra"), ("Pun","Punarvasu"), ("Push","Pushya"),
    ("Asre","Ashlesha"), ("Mag","Magha"), ("PPha","Purva Phalguni"), ("UPh","Uttara Phalguni"),
    ("Has","Hasta"), ("Chi","Chitra"), ("Sva","Svati"), ("Vis","Vishakha"),
    ("Anu","Anuradha"), ("Jye","Jyeshtha"), ("Mula","Mula"), ("PAs","Purva Ashadha"),
    ("UAs","Uttara Ashadha"), ("Sra","Shravana"), ("Dhan","Dhanishtha"), ("Sata","Shatabhisha"),
    ("PBha","Purva Bhadrapada"), ("UBha","Uttara Bhadrapada"), ("Rev","Revati"),
]

NA_PER_SIGN: int = 27
NA_SIZE: float = 360.0 / NA_PER_SIGN    # 13°20'
PADA_SIZE: float = NA_SIZE / 4.0        # 3°20'

# ------------------------------------------------------------
# 角度→サイン／度数／ナクシャトラ
# ------------------------------------------------------------
def sign_index_of(long_deg: float) -> int:
    """0..11 (Ar..Pi) / sidereal long (0..360)"""
    return int(long_deg // 30) % 12

def sign_abbr_of(long_deg: float) -> str:
    return SIGNS[sign_index_of(long_deg)]

def deg_in_sign(long_deg: float) -> float:
    """サイン内度数 0.00..29.99（丸めは行わない。fmtは別途）"""
    return float(long_deg % 30.0)

def nakshatra_of(long_deg: float) -> Tuple[str, str, int]:
    """(abbr, full_name, pada 1..4)"""
    idx = int(long_deg // NA_SIZE) % 27
    abbr, full = NAKSHATRA[idx]
    pada = int((long_deg % NA_SIZE) // PADA_SIZE) + 1
    return abbr, full, pada

def nakshatra_percent_left(long_deg: float) -> float:
    """
    現在のナクシャトラ内の percent_left(0..100)。
    ※ JH に最も近いシンプル式：中間は float のまま、最後だけ round(…, 2)
    """
    pos_in_nak = long_deg % NA_SIZE          # 0 .. < NA_SIZE
    prog = pos_in_nak / NA_SIZE              # 0..1
    left = (1.0 - prog) * 100.0              # 0..100
    # 表示丸めのみ
    return max(0.0, min(100.0, round(left, 2)))

# ------------------------------------------------------------
# Whole Sign house / exalt
# ------------------------------------------------------------
def house_from_signs(asc_si: int, obj_si: int) -> int:
    """Whole Sign: 1..12"""
    return ((obj_si - asc_si) % 12) + 1

def is_exalted(planet: str, sign: str) -> bool:
    return EXALTATION_SIGN.get(planet) == sign

# ------------------------------------------------------------
# 整形ユーティリティ（D1表記用）
# ------------------------------------------------------------
def fmt_deg_2(v: float) -> float:
    """
    度数を小数2桁に丸め、0.00..29.99 にクランプする（D1用）。
    """
    vv = round(float(v), 2)
    if vv >= 30.0:
        vv = 29.99
    if vv < 0:
        vv = 0.00
    return vv

def fmt_speed_3(v: float) -> float:
    """速度（deg/day）を小数3桁で丸める（D1表示用）。"""
    return round(float(v), 3)