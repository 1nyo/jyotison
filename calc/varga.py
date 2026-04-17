# calc/varga.py
from .base import SIGNS, sign_index_of, deg_in_sign

def amsa_degree(din: float, divisions: int) -> float:
    """
    分割図内のサイン内度数（0..30）を返す共通関数
    """
    f = 30.0 / divisions
    deg = (din % f) * divisions
    deg = round(deg, 2)
    if deg >= 30.0:
        return 29.99
    if deg < 0.0:
        return 0.00
    return deg

# -----------------------------------------------
# D2 Hora (Traditional Parāśara)
# -----------------------------------------------

def d2_sign_lord_and_degree(long_deg: float) -> tuple[str, str, float]:
    """
    D2 (Hora) - Traditional Parāśara (BPHS)

    ルール:
      - Sun's Hora  = Leo (Le)  [lord: Su]
      - Moon's Hora = Cancer (Cn) [lord: Mo]

      サイン(30°)を 15° + 15° に分ける。
        * 奇数サイン (Ar, Ge, Le, Li, Sg, Aq):
            0-15°  → Sun Hora (Le)
            15-30° → Moon Hora (Cn)
        * 偶数サイン (Ta, Cn, Vi, Sc, Cp, Pi):
            0-15°  → Moon Hora (Cn)
            15-30° → Sun Hora (Le)

    度数:
      d_long = (deg_in_sign * 2) % 30 として返す（0..30）。
      ※ D2は2サインしかないため、度数は必須ではないが、LLM用途で保持しておくと便利。
    """
    r = sign_index_of(long_deg)     # 0..11
    din = deg_in_sign(long_deg)     # 0..30

    half = int(din // 15.0)         # 0 (0-15), 1 (15-30)
    is_odd_sign = r in (0, 2, 4, 6, 8, 10)  # Ar, Ge, Le, Li, Sg, Aq

    # PyJHora condition:
    # if (odd and half==0) or (even and half==1): Sun Hora else Moon Hora
    sun_hora = (is_odd_sign and half == 0) or ((not is_odd_sign) and half == 1)

    if sun_hora:
        sign = "Le"
        lord = "Su"
    else:
        sign = "Cn"
        lord = "Mo"

    d_long = round((din * 2.0) % 30.0, 2)
    if d_long >= 30.0:
        d_long = 29.99
    if d_long < 0.0:
        d_long = 0.00

    return sign, lord, d_long


def build_d2_hora(asc_long: float, planets_long: dict) -> dict:
    """
    D2は house を出さない（Cancer/Leo の2択で Whole Sign house が解釈上ノイズになりやすい）。
    その代わり、sign と lord（Su/Mo）を主情報として返す。
    """
    asc_sign, asc_lord, asc_deg = d2_sign_lord_and_degree(asc_long)

    out_pl = {}
    for p, lon in planets_long.items():
        s, l, d = d2_sign_lord_and_degree(lon)
        out_pl[p] = {"sign": s, "degree": d, "lord": l}

    return {
        "Asc": {"sign": asc_sign, "degree": asc_deg, "lord": asc_lord},
        "planets": out_pl
    }

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

def d3_sign_and_degree(long_deg: float) -> tuple[str, float]:
    """
    Drekkana (D3) — Traditional Parasara Method に準拠。
      - 各サイン(30°)を 10° * 3 に分割
      - サイン内度数 0〜10°  → 元のサイン
      - サイン内度数 10〜20° → 5番目のサイン
      - サイン内度数 20〜30° → 9番目のサイン
    """
    r   = sign_index_of(long_deg)   # 0..11 (Ar..Pi)
    din = deg_in_sign(long_deg)     # 0..30

    dvf = 3
    part = int(din // (30.0 / dvf)) # 0,1,2

    # 0 → 同じサイン, 1 → 5番目, 2 → 9番目
    si = (r + part * 4) % 12        # 4 = 12 / 3
    sign = SIGNS[si]
    deg  = amsa_degree(din, dvf)

    return sign, deg

# ======================================================
# D4 Chaturthamsa
# ======================================================

def d4_sign_and_degree(long_deg: float) -> tuple[str, float]:
    """
    D4 (Chaturthamsa) — Traditional Parasara
    30° を 7.5° * 4 に分割し、
      part=0: +0
      part=1: +3 signs
      part=2: +6 signs
      part=3: +9 signs
    を割り当てる。
    """
    r   = sign_index_of(long_deg)     # 0..11
    din = deg_in_sign(long_deg)       # 0..30

    dvf = 4
    part = int(din // (30.0 / dvf))   # 0..3

    # f2 = 3 → move 3 signs per part
    si = (r + part * 3) % 12
    sign = SIGNS[si]
    deg  = amsa_degree(din, dvf)

    return sign, deg

# ======================================================
# D7 Saptamsa
# ======================================================

def d7_sign_and_degree(long_deg: float) -> tuple[str, float]:
    """
    Saptamsa (D7)
    サイン + サイン内度数（0..30）を返す
    """
    r   = sign_index_of(long_deg)   # 0..11
    din = deg_in_sign(long_deg)     # 0..30

    dvf = 7
    part = int(din // (30.0 / dvf)) # amsa index 0..6

    # 奇数サイン: Ar, Ge, Le, Li, Sg, Aq
    if r not in (1, 3, 5, 7, 9, 11):
        base = r
    else:
        base = (r + 6) % 12         # 偶数サイン

    sign = SIGNS[(base + part) % 12]
    deg  = amsa_degree(din, dvf)

    return sign, deg

# ======================================================
# D10 Dasamsa
# ======================================================

def d10_sign_and_degree(long_deg: float) -> tuple[str, float]:
    """
    Daśāṁśa (D10) — Parāśara式
    30°を3°*10に分割し、
      - 奇数サイン (Ar, Ge, Le, Li, Sg, Aq) では、そのサイン自身を起点に順行
      - 偶数サイン (Ta, Cn, Vi, Sc, Cp, Pi) では、そのサインから数えて9番目のサインを起点に順行
    """
    r   = sign_index_of(long_deg)   # 0..11 (Ar..Pi)
    din = deg_in_sign(long_deg)     # 0..30

    dvf = 10
    part = int(din // (30.0 / dvf)) # 0..9

    # 奇数サイン: Ar, Ge, Le, Li, Sg, Aq
    if r in (0, 2, 4, 6, 8, 10):
        base = r
    else:
        # 偶数サイン: Ta, Cn, Vi, Sc, Cp, Pi → 9番目のサインを起点
        base = (r + 8) % 12

    sign = SIGNS[(base + part) % 12]
    deg  = amsa_degree(din, dvf)

    return sign, deg

# ======================================================
# D12 Dwadasamsa
# ======================================================

def d12_sign_and_degree(long_deg: float) -> tuple[str, float]:
    """
    D12 (Dwadasamsa) — Traditional Parāśaraと整合。
    30° を 2.5° * 12 に分割し、
      l = floor(din / 2.5) (0..11)
      D12 sign = 元の sign から l つ進めたサイン
    """
    r   = sign_index_of(long_deg)  # 0..11
    din = deg_in_sign(long_deg)    # 0..30

    dvf = 12
    l  = int(din // (30.0 / dvf))            # 0..11

    si = (r + l) % 12

    sign = SIGNS[si]
    deg  = amsa_degree(din, dvf)

    return sign, deg

# ======================================================
# D16 Shodasamsa
# ======================================================

def d16_sign_and_degree(long_deg: float) -> tuple[str, float]:
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

    dvf = 16
    l  = int(din // (30.0 / dvf))             # 0..15

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

    sign = SIGNS[si]
    deg  = amsa_degree(din, dvf)

    return sign, deg

# ======================================================
# D20 Vimsamsa
# =====================================================

def d20_sign_and_degree(long_deg: float) -> tuple[str, float]:
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
    dvf = 20
    part = int(din // (30.0 / dvf))              # 0..19

    if r in (0, 3, 6, 9):       # Movable: Ar, Cn, Li, Cp
        base = 0                # Aries
    elif r in (1, 4, 7, 10):    # Fixed: Ta, Le, Sc, Aq
        base = 8                # Sagittarius
    else:                       # Dual: Ge, Vi, Sg, Pi
        base = 4                # Leo

    si = (base + part) % 12

    sign = SIGNS[si]
    deg  = amsa_degree(din, dvf)

    return sign, deg

# ======================================================
# D24 Siddhamsa
# =====================================================

def d24_sign_and_degree(long_deg: float) -> tuple[str, float]:
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
    dvf = 24
    part = int(din // (30.0 / dvf))           # 0..23

    # 奇数サイン: Ar, Ge, Le, Li, Sg, Aq -> index: 0,2,4,6,8,10
    if r in (0, 2, 4, 6, 8, 10):
        base = SIGNS.index("Le")  # Leo
    else:
        base = SIGNS.index("Cn")  # Cancer

    si = (base + part) % 12

    sign = SIGNS[si]
    deg  = amsa_degree(din, dvf)

    return sign, deg

# ======================================================
# D27 Nakshatramsa
# ======================================================

def d27_sign_and_degree(long_deg: float) -> tuple[str, float]:
    """
    Nakshatramsa (D27) — Traditional Parāśara

    実装ロジック:
      dvf = 27
      f1 = 30 / 27 = 1.111...°

      l = floor(deg_in_sign / f1)  # 0..26

      起点:
        - Fire  (Ar, Le, Sg): l % 12
        - Earth (Ta, Vi, Cp): (l + 3) % 12   [Cancer 起点]
        - Air   (Ge, Li, Aq): (l + 6) % 12
        - Water (Cn, Sc, Pi): (l + 9) % 12
    """
    r   = sign_index_of(long_deg)   # 0..11 (Ar..Pi)
    din = deg_in_sign(long_deg)     # 0..30

    dvf = 27
    l   = int(din // (30.0 / dvf))             # 0..26

    # Fire signs: Ar(0), Le(4), Sg(8)
    if r in (0, 4, 8):
        si = l % 12

    # Earth signs: Ta(1), Vi(5), Cp(9)
    elif r in (1, 5, 9):
        si = (l + 3) % 12

    # Air signs: Ge(2), Li(6), Aq(10)
    elif r in (2, 6, 10):
        si = (l + 6) % 12

    # Water signs: Cn(3), Sc(7), Pi(11)
    else:
        si = (l + 9) % 12

    sign = SIGNS[si]
    deg  = amsa_degree(din, dvf)

    return sign, deg

# ======================================================
# D30 Trimshamsa
# ==================================================

def d30_sign_and_degree(long_deg: float) -> tuple[str, float]:
    """
    D30 Trimshamsa — Traditional Parāśara
    - サイン：不等分割（5,5,8,7,5）で決定
    - degree： (D1 サイン内度数 x 30) % 30
    """

    r   = sign_index_of(long_deg)   # 0..11
    din = deg_in_sign(long_deg)     # 0..30

    deg = round((din * 30.0) % 30.0, 2)
    if deg >= 30.0:
        deg = 29.99
    if deg < 0.0:
        deg = 0.00

    odd = [
        (0.0, 5.0, 0),   # Ar (Mars)
        (5.0, 10.0, 10), # Aq (Saturn)
        (10.0, 18.0, 8), # Sg (Jupiter)
        (18.0, 25.0, 2), # Ge (Mercury)
        (25.0, 30.0, 6), # Li (Venus)
    ]

    even = [
        (0.0, 5.0, 1),   # Ta (Venus)
        (5.0, 12.0, 5),  # Vi (Mercury)
        (12.0, 20.0, 11),# Pi (Jupiter)
        (20.0, 25.0, 9), # Cp (Saturn)
        (25.0, 30.0, 7), # Sc (Mars)
    ]

    if r in (0, 2, 4, 6, 8, 10):  # odd signs
        table = odd
    else:
        table = even

    for l_min, l_max, si in table:
        if l_min <= din <= l_max:
            return SIGNS[si % 12], deg

    # 理論上ここには来ない
    return "Ar", deg

# ======================================================
# D40 Khavedamsa
# ======================================================

def d40_sign_and_degree(long_deg: float) -> tuple[str, float]:
    """
    Khavedamsa (D40) — Traditional Parāśara

    ロジック:
      dvf = 40
      f1  = 30 / 40 = 0.75°
      l   = floor(deg_in_sign / f1)  # 0..39

      奇数サイン: part from Aries -> r = l % 12
      偶数サイン: part from Libra -> r = (l + 6) % 12
    """
    r   = sign_index_of(long_deg)   # 0..11 (Ar..Pi)
    din = deg_in_sign(long_deg)     # 0..30

    dvf = 40
    l   = int(din // (30.0 / dvf))            # 0..39

    # even_signs: Ta(1), Cn(3), Vi(5), Sc(7), Cp(9), Pi(11)
    if r in (1, 3, 5, 7, 9, 11):
        si = (l + 6) % 12           # part from Libra
    else:
        si = l % 12                 # part from Aries

    sign = SIGNS[si]
    deg  = amsa_degree(din, dvf)

    return sign, deg

# ======================================================
# D45 Akshavedamsa
# ======================================================

def d45_sign_and_degree(long_deg: float) -> tuple[str, float]:
    """
    Akshavedamsa (D45) — Traditional Parāśara

    ロジック:
      dvf = 45
      f1  = 30 / 45 = 0.666666...°
      l   = floor(deg_in_sign / f1)  # 0..44

      起点:
        - Movable signs (Ar, Cn, Li, Cp): r = l % 12
        - Fixed signs   (Ta, Le, Sc, Aq): r = (l + 4) % 12
        - Dual signs    (Ge, Vi, Sg, Pi): r = (l + 8) % 12
    """
    r   = sign_index_of(long_deg)   # 0..11 (Ar..Pi)
    din = deg_in_sign(long_deg)     # 0..30

    dvf = 45
    l   = int(din // (30.0 / dvf))             # 0..44

    # Fixed signs: Ta(1), Le(4), Sc(7), Aq(10)
    if r in (1, 4, 7, 10):
        si = (l + 4) % 12

    # Dual signs: Ge(2), Vi(5), Sg(8), Pi(11)
    elif r in (2, 5, 8, 11):
        si = (l + 8) % 12

    # Movable signs: Ar(0), Cn(3), Li(6), Cp(9)
    else:
        si = l % 12

    sign = SIGNS[si]
    deg  = amsa_degree(din, dvf)

    return sign, deg

# ======================================================
# D60 Shastyamsa
# ======================================================

def d60_sign_and_degree(long_deg: float) -> tuple[str, float]:
    """
    Ṣaṣṭiāṁśa (D60)
    30°を0.5°*60に分け、【各サイン自身】を起点として順行で加算する。
      si = (rashi_index + floor(deg_in_sign/0.5)) % 12

    例）Cn 23°30':
        r = Cn(3), part = floor(23.5 / 0.5) = 47
        si = (3 + 47) % 12 = 2 → Ge
    """
    r = sign_index_of(long_deg)       # 0..11 (Ar..Pi)
    din = deg_in_sign(long_deg)       # 0..30
    dvf = 60
    part = int(din // (30.0 / dvf))             # 0..59
    si = (r + part) % 12

    sign = SIGNS[si]
    deg  = amsa_degree(din, dvf)

    return sign, deg


# ======================================================
# Varga 共通ビルダー（D1,D9 以外すべてこれで生成）
# ======================================================

VARGA_SIGN_FUNC = {
    "D3":  d3_sign_and_degree,
    "D4":  d4_sign_and_degree,
    "D7":  d7_sign_and_degree,
    "D10": d10_sign_and_degree,
    "D12": d12_sign_and_degree,
    "D16": d16_sign_and_degree,
    "D20": d20_sign_and_degree,
    "D24": d24_sign_and_degree,
    "D27": d27_sign_and_degree,
    "D30": d30_sign_and_degree,
    "D40": d40_sign_and_degree,
    "D45": d45_sign_and_degree,
    "D60": d60_sign_and_degree,
}

from .base import house_from_signs

def build_varga(name: str, asc_long: float, planets_long: dict) -> dict:
    """
    Varga chart builder (calculation layer).

    Design:
    - All varga charts carry degree information internally.
    - Output masking (e.g. removing degree) is handled later
      by output/filters.py.
    """

    # D2 Hora は特殊
    if name == "D2":
        return build_d2_hora(asc_long, planets_long)

    fn = VARGA_SIGN_FUNC.get(name)
    if fn is None:
        raise ValueError(f"Unsupported varga: {name}")

    # Ascendant
    asc_sign, asc_deg = fn(asc_long)
    asc_si = SIGNS.index(asc_sign)

    # Planets
    out_pl = {}
    for p, lon in planets_long.items():
        psign, pdeg = fn(lon)
        psi = SIGNS.index(psign)
        house = house_from_signs(asc_si, psi)

        out_pl[p] = {
            "sign": psign,
            "degree": pdeg,
            "house": house
        }

    return {
        "Asc": {
            "sign": asc_sign,
            "degree": asc_deg
        },
        "planets": out_pl
    }
