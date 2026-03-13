# calc/varga.py
from .base import SIGNS, sign_index_of, deg_in_sign

def navamsa_long(long_deg: float) -> float:
    """
    D9（Navamsa）の絶対黄経（0..360）を返す正統法。
    標準手順（BPHS整合）:
        absolute_longitude * 9 → modulo 360
    これにより、JH の D-9（Traditional）とサイン/度数が一致します。
    """
    v = (float(long_deg) * 9.0) % 360.0
    # 念のため負値を回避
    if v < 0:
        v += 360.0
    return v

def d9_sign_and_degree(long_deg: float) -> tuple[str, float]:
    """
    入力: D1 の絶対黄経（0..360）
    出力: (D9サイン略号, D9サイン内度数 0..30) 〔小数2桁、30.00に上がらないようクランプ〕
    手順:
      1) d9_abs = (long * 9) % 360
      2) sign = floor(d9_abs / 30)
      3) degree = (d9_abs % 30) を小数2桁丸め（上限29.99）
    """
    d9_abs = navamsa_long(long_deg)
    si = int(d9_abs // 30) % 12
    sign = SIGNS[si]

    deg = round(d9_abs % 30.0, 2)
    if deg >= 30.0:
        deg = 29.99
    if deg < 0.0:
        deg = 0.00

    return sign, deg

def vimsamsa_sign(long_deg: float) -> str:
    """
    Vimśāṁśa (D20) — Parāśara系（JH “D-20 (Trd)” に一致）
    30°を1.5°×20に分け、モダリティ（動/不動/両義）に応じた起点から順行加算。

    起点:
      - 動 (Ar, Cn, Li, Cp): Aries(0)
      - 不動 (Ta, Le, Sc, Aq): Sagittarius(8)
      - 両義 (Ge, Vi, Sg, Pi): Leo(4)
    """
    r = sign_index_of(long_deg)         # 0..11 (Ar..Pi)
    din = deg_in_sign(long_deg)         # 0..30
    part = int(din // 1.5)              # 0..19

    if r in (0, 3, 6, 9):       # Movable: Ar, Cn, Li, Cp
        base = 0                # Aries
    elif r in (1, 4, 7, 10):    # Fixed: Ta, Le, Sc, Aq
        base = 8                # Sagittarius
    else:                       # Dual: Ge, Vi, Sg, Pi
        base = 4                # Leo

    si = (base + part) % 12
    return SIGNS[si]

def shastyamsa_sign(long_deg: float) -> str:
    """
    Ṣaṣṭiāṁśa (D60) — JH “D-60 (Trd)” と一致する実装。
    30°を0.5°×60に分け、【各サイン自身】を起点として順行で加算する。
      si = (rashi_index + floor(deg_in_sign/0.5)) % 12

    例）Cn 23°30′:
        r = Cn(3), part = floor(23.5 / 0.5) = 47
        si = (3 + 47) % 12 = 2 → Ge
    """
    r = sign_index_of(long_deg)       # 0..11 (Ar..Pi)
    din = deg_in_sign(long_deg)       # 0..30
    part = int(din // 0.5)            # 0..59
    si = (r + part) % 12
    return SIGNS[si]
