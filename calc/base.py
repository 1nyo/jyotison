# calc/base.py
from dataclasses import dataclass
from typing import Dict, Tuple, List

# ------------------------------------------------------------
# 基本定義
# ------------------------------------------------------------

SIGNS: List[str] = ["Ar","Ta","Ge","Cn","Le","Vi","Li","Sc","Sg","Cp","Aq","Pi"]
PLANETS: List[str] = ["Su","Mo","Ma","Me","Ju","Ve","Sa","Ra","Ke"]

# ------------------------------------------------------------
# 占星術データ：Exaltation / Debilitation / MT / ロード / 友敵
# ------------------------------------------------------------

# Exaltation（高揚サイン）
EXALTATION_SIGN: Dict[str, str] = {
    "Su": "Ar", "Mo": "Ta", "Ma": "Cp", "Me": "Vi",
    "Ju": "Cn", "Ve": "Pi", "Sa": "Li", "Ra": "Ta", "Ke": "Sc"
}

# Debilitation（減衰サイン）＝高揚の対向
DEBILITATION_SIGN: Dict[str, str] = {
    p: SIGNS[(SIGNS.index(s) + 6) % 12] for p, s in EXALTATION_SIGN.items()
}

# サイン → 支配星（D1 Lords）
SIGN_LORD: Dict[str, str] = {
    "Ar": "Ma", "Ta": "Ve", "Ge": "Me", "Cn": "Mo", "Le": "Su", "Vi": "Me",
    "Li": "Ve", "Sc": "Ma", "Sg": "Ju", "Cp": "Sa", "Aq": "Sa", "Pi": "Ju",
}

# Moolatrikona レンジ（sign, start_deg, end_deg）
MOOLATRIKONA_RANGE: Dict[str, Tuple[str, float, float]] = {
    "Su": ("Le", 0.0, 20.0),
    "Mo": ("Ta", 3.0, 30.0),
    "Ma": ("Ar", 0.0, 12.0),
    "Me": ("Vi", 15.0, 20.0),
    "Ju": ("Sg", 0.0, 10.0),
    "Ve": ("Li", 0.0, 15.0),
    "Sa": ("Aq", 0.0, 20.0),
    # Ra/Ke: MTなし
}

# 自然友好表
FRIENDS: Dict[str, List[str]] = {
    "Su": ["Mo", "Ma", "Ju"],
    "Mo": ["Su", "Me"],
    "Ma": ["Su", "Mo", "Ju"],
    "Me": ["Su", "Ve"],
    "Ju": ["Su", "Mo", "Ma"],
    "Ve": ["Me", "Sa"],
    "Sa": ["Me", "Ve"],
    "Ra": [],
    "Ke": [],
}

# 自然敵対表
ENEMIES: Dict[str, List[str]] = {
    "Su": ["Ve", "Sa"],
    "Mo": [],
    "Ma": ["Me"],
    "Me": ["Mo"],
    "Ju": ["Me", "Ve"],
    "Ve": ["Su", "Mo"],
    "Sa": ["Su", "Mo", "Ma"],
    "Ra": [],
    "Ke": [],
}

# ------------------------------------------------------------
# ナクシャトラ（アビジュテーション）データ
# ------------------------------------------------------------

# (abbr, full_name)
NAKSHATRA: List[Tuple[str, str]] = [
    ("Asw","Ashwini"), ("Bha","Bharani"), ("Kri","Krittika"), ("Roh","Rohini"),
    ("Mri","Mrigashira"), ("Ard","Ardra"), ("Pun","Punarvasu"), ("Push","Pushya"),
    ("Asre","Ashlesha"), ("Mag","Magha"), ("PPha","Purva Phalguni"), ("UPh","Uttara Phalguni"),
    ("Has","Hasta"), ("Chi","Chitra"), ("Sva","Svati"), ("Vis","Vishakha"),
    ("Anu","Anuradha"), ("Jye","Jyeshtha"), ("Mula","Mula"), ("PAs","Purva Ashadha"),
    ("UAs","Uttara Ashadha"), ("Sra","Shravana"), ("Dhan","Dhanishtha"), ("Sata","Shatabhisha"),
    ("PBha","Purva Bhadrapada"), ("UBha","Uttara Bhadrapada"), ("Rev","Revati"),
]

# ナクシャトラロード（Ketu→Venus→Sun→Moon→…）
_NAK_LORD_SEQ = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
NAK_LORDS: List[str] = (_NAK_LORD_SEQ * 3)[:27]

def nakshatra_lord_by_index(idx: int) -> str:
    return NAK_LORDS[idx % 27]

# ナクシャトラ定数
NA_PER_SIGN: int = 27
NA_SIZE: float = 360.0 / NA_PER_SIGN
PADA_SIZE: float = NA_SIZE / 4.0

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
    pos = long_deg % NA_SIZE
    prog = pos / NA_SIZE
    left = (1.0 - prog) * 100.0
    return max(0.0, min(100.0, round(left, 2)))

# ------------------------------------------------------------
# Whole Sign house
# ------------------------------------------------------------

def house_from_signs(asc_si: int, obj_si: int) -> int:
    """Whole Sign: 1..12"""
    return ((obj_si - asc_si) % 12) + 1

# ------------------------------------------------------------
# 整形ユーティリティ
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