# calc/varga.py
from .base import SIGNS, sign_index_of, deg_in_sign

# -----------------------------------------------
# D9 Navamsa
# -----------------------------------------------

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
    出力: (D9サイン略号, D9サイン内度数 0..30) [小数2桁、30.00に上がらないようクランプ]
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

# ======================================================
# D3 Drekkana
# ======================================================

def drekkana_sign(long_deg: float) -> str:
    """
    Drekkana (D3) — PVR/Traditional Parasara Method に準拠。
    PyJHora の _drekkana_chart_parasara と一致させる。

      - 各サイン(30°)を 10° * 3 に分割
      - サイン内度数 0〜10°  → 元のサイン
      - サイン内度数 10〜20° → 5番目のサイン
      - サイン内度数 20〜30° → 9番目のサイン
    """
    r   = sign_index_of(long_deg)   # 0..11 (Ar..Pi)
    din = deg_in_sign(long_deg)     # 0..30

    f1 = 30.0 / 3.0                 # 10.0
    l  = int(din // f1)             # 0,1,2

    # 0 → 同じサイン, 1 → 5番目, 2 → 9番目
    si = (r + l * 4) % 12           # 4 = 12 / 3
    return SIGNS[si]

# ======================================================
# D4 Chaturthamsa
# ======================================================

def chaturthamsa_sign(long_deg: float) -> str:
    """
    D4 (Chaturthamsa) — Traditional Parasara (PyJHora _chaturthamsa_parasara と整合)
    30° を 7.5° * 4 に分割し、
      part=0: +0
      part=1: +3 signs
      part=2: +6 signs
      part=3: +9 signs
    を割り当てる。
    """
    r   = sign_index_of(long_deg)     # 0..11
    din = deg_in_sign(long_deg)       # 0..30

    f1 = 30.0 / 4.0                   # 7.5°
    part = int(din // f1)             # 0..3

    # f2 = 3 → move 3 signs per part
    si = (r + part * 3) % 12
    return SIGNS[si]

# ======================================================
# D7 Saptamsa
# ======================================================

def saptamsa_sign(long_deg: float) -> str:
    """
    Saptamsa (D7) — PyJHora の Traditional Parasara (chart_method=1) と整合。
    30° を 7 等分し、
      - 奇数サイン: そのサイン自身を起点に区画番号ぶん進める
      - 偶数サイン: そのサインから7番目のサインを起点に区画番号ぶん進める
    """
    r   = sign_index_of(long_deg)   # 0..11 (Ar..Pi)
    din = deg_in_sign(long_deg)     # 0..30

    f1 = 30.0 / 7.0                 # 1 区画 ≒ 4.2857°
    l = int(din // f1)              # 区画 index 0..6

    # 奇数サイン: Ar, Ge, Le, Li, Sg, Aq
    if r not in (1, 3, 5, 7, 9, 11):  # even_signs が Ta,Cn,Vi,Sc,Cp,Pi なのでその逆
        base = r
    else:
        base = (r + 6) % 12    # 偶数サイン = 7th from Sign（+6）
 
    si = (base + l) % 12
    return SIGNS[si]

# ======================================================
# D10 Dasamsa
# ======================================================

def dasamsa_sign(long_deg: float) -> str:
    """
    Daśāṁśa (D10) — Parāśara式（JH \"D-10 (Trd)\" と整合）。
    30°を3°*10に分割し、
      - 奇数サイン (Ar, Ge, Le, Li, Sg, Aq) では、そのサイン自身を起点に順行
      - 偶数サイン (Ta, Cn, Vi, Sc, Cp, Pi) では、そのサインから数えて9番目のサインを起点に順行
    """
    r   = sign_index_of(long_deg)   # 0..11 (Ar..Pi)
    din = deg_in_sign(long_deg)     # 0..30
    part = int(din // 3.0)          # 0..9

    # 奇数サイン: Ar, Ge, Le, Li, Sg, Aq
    if r in (0, 2, 4, 6, 8, 10):
        base = r
    else:
        # 偶数サイン: Ta, Cn, Vi, Sc, Cp, Pi → 9番目のサインを起点
        base = (r + 8) % 12

    si = (base + part) % 12
    return SIGNS[si]

# ======================================================
# D12 Dwadasamsa
# ======================================================

def dwadasamsa_sign(long_deg: float) -> str:
    """
    D12 (Dwadasamsa) — Traditional Parāśara / PyJHora dwadasamsa_chart(chart_method=1) と整合。
    30° を 2.5° * 12 に分割し、
      l = floor(din / 2.5) (0..11)
      D12 sign = 元の sign から l つ進めたサイン
    """
    r   = sign_index_of(long_deg)  # 0..11
    din = deg_in_sign(long_deg)    # 0..30

    f1 = 30.0 / 12.0               # 2.5°
    l  = int(din // f1)            # 0..11

    si = (r + l) % 12
    return SIGNS[si]

# ======================================================
# D16 Shodasamsa
# ======================================================

def shodasamsa_sign(long_deg: float) -> str:
    """
    D16 (Shodasamsa / Kalamsa) — Traditional Parāśara / PyJHora shodasamsa_chart(chart_method=1) と整合。
    30° を 1.875° * 16 に分割し、
      l = floor(din / (30/16)) (0..15)
      r0 = l % 12 を基準として、サインのモダリティでオフセットする。

      - Movable (Ar,Cn,Li,Cp): r = r0
      - Fixed   (Ta,Le,Sc,Aq): r = (r0 + 4) % 12
      - Dual    (Ge,Vi,Sg,Pi): r = (r0 + 8) % 12
    """
    r   = sign_index_of(long_deg)   # 0..11 (Ar..Pi)
    din = deg_in_sign(long_deg)     # 0..30

    f1 = 30.0 / 16.0                # 1.875°
    l  = int(din // f1)             # 0..15

    # ベース: Aries 始まり 12サインを l%12 でローテーション
    r0 = l % 12

    # モダリティ
    # Movable: Ar(0), Cn(3), Li(6), Cp(9)
    # Fixed:   Ta(1), Le(4), Sc(7), Aq(10)
    # Dual:    Ge(2), Vi(5), Sg(8), Pi(11)
    if r in (1, 4, 7, 10):          # Fixed
        si = (r0 + 4) % 12
    elif r in (2, 5, 8, 11):        # Dual
        si = (r0 + 8) % 12
    else:                           # Movable
        si = r0

    return SIGNS[si]

# ======================================================
# D20 Vimsamsa
# =====================================================

def vimsamsa_sign(long_deg: float) -> str:
    """
    Vimśāṁśa (D20) — Parāśara系（JH “D-20 (Trd)” に一致）
    30°を1.5°*20に分け、モダリティ（動/不動/両義）に応じた起点から順行加算。

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

# ======================================================
# D24 Siddhamsa
# =====================================================

def siddhamsa_sign(long_deg: float) -> str:
    """
    Siddhamsa / Chaturvimshamsa (D24) — Parāśara式。
    各サイン(30°)を1.25°*24に分割。

    ルール（広く用いられる解釈）:
      - 奇数サイン (Ar, Ge, Le, Li, Sg, Aq):
          起点サイン = Leo (Le)
      - 偶数サイン (Ta, Cn, Vi, Sc, Cp, Pi):
          起点サイン = Cancer (Cn)

      サイン内度数 din から amsa index = floor(din / 1.25)（0..23）を求め、
      起点サインから zodiac 順に amsa 分進めたサインを D24 sign とする。
    """
    r   = sign_index_of(long_deg)   # 0..11 (Ar..Pi)
    din = deg_in_sign(long_deg)     # 0..30
    f1 = 30.0 / 24.0                # 1.25°
    part = int(din // f1)           # 0..23

    # 奇数サイン: Ar, Ge, Le, Li, Sg, Aq -> index: 0,2,4,6,8,10
    if r in (0, 2, 4, 6, 8, 10):
        base = SIGNS.index("Le")  # Leo
    else:
        base = SIGNS.index("Cn")  # Cancer

    si = (base + part) % 12
    return SIGNS[si]

# ======================================================
# D30 Trimshamsa
# ==================================================

def trimsamsa_sign(long_deg: float) -> str:
    """
    Trimshamsa (D30) — Parāśara式。
    30°を 5,5,8,7,5 度の 5 区画に分割し、奇数/偶数サインで
    惑星順序を入れ替え、その惑星の男性/女性サインを D30 サインとする。
    """

    r   = sign_index_of(long_deg)   # 0..11 (Ar..Pi)
    din = deg_in_sign(long_deg)     # 0..30

    # 奇数サイン（男性サイン）: Ar, Ge, Le, Li, Sg, Aq
    if r in (0, 2, 4, 6, 8, 10):
        # 度数 -> 惑星 (Mars, Saturn, Jupiter, Mercury, Venus)
        if din < 5.0:
            # Mars → male sign: Ar
            return "Ar"
        elif din < 10.0:
            # Saturn → male sign: Aq
            return "Aq"
        elif din < 18.0:
            # Jupiter → male sign: Sg
            return "Sg"
        elif din < 25.0:
            # Mercury → male sign: Ge
            return "Ge"
        else:
            # Venus → male sign: Li
            return "Li"

    # 偶数サイン（女性サイン）: Ta, Cn, Vi, Sc, Cp, Pi
    else:
        # 惑星順序を逆に (Venus, Mercury, Jupiter, Saturn, Mars)
        if din < 5.0:
            # Venus → female sign: Ta
            return "Ta"
        elif din < 10.0:
            # Mercury → female sign: Vi
            return "Vi"
        elif din < 18.0:
            # Jupiter → female sign: Pi
            return "Pi"
        elif din < 25.0:
            # Saturn → female sign: Cp
            return "Cp"
        else:
            # Mars → female sign: Sc
            return "Sc"

# ======================================================
# D60 Shastyamsa
# ======================================================

def shastyamsa_sign(long_deg: float) -> str:
    """
    Ṣaṣṭiāṁśa (D60) — JH “D-60 (Trd)” と一致する実装。
    30°を0.5°*60に分け、【各サイン自身】を起点として順行で加算する。
      si = (rashi_index + floor(deg_in_sign/0.5)) % 12

    例）Cn 23°30':
        r = Cn(3), part = floor(23.5 / 0.5) = 47
        si = (3 + 47) % 12 = 2 → Ge
    """
    r = sign_index_of(long_deg)       # 0..11 (Ar..Pi)
    din = deg_in_sign(long_deg)       # 0..30
    f1 = 30.0 / 60.0                  # 0.5°
    part = int(din // f1)             # 0..59
    si = (r + part) % 12
    return SIGNS[si]


# ======================================================
# Varga 共通ビルダー（D1,D9 以外すべてこれで生成）
# ======================================================

VARGA_SIGN_FUNC = {
    "D3":  drekkana_sign,
    "D4":  chaturthamsa_sign,
    "D7":  saptamsa_sign,
    "D10": dasamsa_sign,
    "D12": dwadasamsa_sign,
    "D16": shodasamsa_sign,
    "D20": vimsamsa_sign,
    "D24": siddhamsa_sign,
    "D30": trimsamsa_sign,
    "D60": shastyamsa_sign,
}

from .base import house_from_signs

def build_varga(name: str, asc_long: float, planets_long: dict) -> dict:
    fn = VARGA_SIGN_FUNC[name]

    asc_sign = fn(asc_long)
    asc_si = SIGNS.index(asc_sign)

    out_pl = {}
    for p, lon in planets_long.items():
        psign = fn(lon)
        psi = SIGNS.index(psign)
        house = house_from_signs(asc_si, psi)
        out_pl[p] = {"sign": psign, "house": house}

    return {"Asc": {"sign": asc_sign}, "planets": out_pl}
