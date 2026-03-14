# calc/jaimini.py
from typing import Dict, List, Tuple, Optional, Literal

from .base import SIGNS, SIGN_LORD
from .varga import d9_sign_and_degree

# ------------------------------------------------------------
# Chara Karaka
# ------------------------------------------------------------

KARAKAS_8 = ["AK", "AmK", "BK", "MK", "PiK", "PK", "GK", "DK"]
KARAKAS_7 = ["AK", "AmK", "BK", "MK",          "PK", "GK", "DK"]  # PiK を除外

# タイブレークの安定順（完全一致時の最終決定）
TIEBREAK_PLANET_ORDER = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra"]

def _rank_key(planet: str, deg_in_sign: float) -> float:
    """
    ランキング主キー：
      - 通常：度数が大きいほど上位（降順）
      - Rahu：度数が小さいほど上位（逆順）→ (30 - deg)
    """
    v = float(deg_in_sign)
    return 30.0 - v if planet == "Ra" else v

def _planet_order_rank(planet: str) -> int:
    """完全一致時の固定順優先度（小さいほど上に来る）"""
    try:
        return TIEBREAK_PLANET_ORDER.index(planet)
    except ValueError:
        return len(TIEBREAK_PLANET_ORDER)

def assign_chara_karaka(
    deg_by_planet: Dict[str, float],
    mode: Literal[8, 7],
    abs_long_by_planet: Optional[Dict[str, float]] = None,
) -> Dict[str, str]:
    """
    チャラ・カラカ割当（7/8対応）。
    入力:
      - deg_by_planet: 惑星→サイン内度数(0..30)（丸め前推奨）
      - mode: 8 or 7（7は PiK 無し・Ra 除外）
      - abs_long_by_planet: 惑星→絶対黄経(0..360)（任意。同点時の安定化に使用）
    出力:
      - {"AK":"..","AmK":"..",...}
    """
    if mode == 8:
        targets = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra"]
        labels = KARAKAS_8
    else:
        targets = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]  # Ra 除外
        labels = KARAKAS_7

    items: List[Tuple[str, float, float, int]] = []
    for p in targets:
        if p not in deg_by_planet:
            continue
        din = float(deg_by_planet[p])
        primary = _rank_key(p, din)
        abs_lon = float(abs_long_by_planet[p]) if abs_long_by_planet and p in abs_long_by_planet else -1.0
        tie_rank = -_planet_order_rank(p)  # sort(reverse=True) と親和させるため符号反転
        items.append((p, primary, abs_lon, tie_rank))

    # 主キー（primary）の降順 → abs_lon の降順 → 固定順の降順（tie_rank は負号）
    items.sort(key=lambda t: (t[1], t[2], t[3]), reverse=True)

    out: Dict[str, str] = {}
    for i in range(min(len(items), len(labels))):
        out[labels[i]] = items[i][0]
    return out

# ------------------------------------------------------------
# Karakamsha（AK の D9 サイン）
# ------------------------------------------------------------

def karakamsa_sign_for_ak(
    abs_long_by_planet: Dict[str, float],
    ak_planet: Optional[str],
) -> Optional[str]:
    """
    AKへ Karakamsha を返す（AK の D9 サイン略号）。
    依存: calc.varga.d9_sign_and_degree()
    """
    if not ak_planet:
        return None
    lon = abs_long_by_planet.get(ak_planet)
    if lon is None:
        return None
    sign, _ = d9_sign_and_degree(lon)
    return sign

# ------------------------------------------------------------
# Arudha（AL/UL）
# ------------------------------------------------------------

def _sign_index(sign: str) -> int:
    return SIGNS.index(sign)

def _sign_of_house(asc_sign: str, house_no: int) -> str:
    """
    Whole Sign: Ascサインを1室として house_no(1..12) のサイン略号を返す。
    """
    asc_si = _sign_index(asc_sign)
    return SIGNS[(asc_si + (house_no - 1)) % 12]

def _distance(h_from: int, h_to: int) -> int:
    """
    house番号(1..12) 間の距離 d を返す（1..12）。
    同一なら 1、対向なら 7。
    """
    return ((h_to - h_from) % 12) + 1

def _lords_by_house_from_asc(asc_sign: str) -> Dict[str, str]:
    """
    D1 の 'lords' が無い場合の代替：Ascサインから各ハウスの支配星を生成（Whole Sign）。
    """
    out: Dict[str, str] = {}
    for h in range(1, 13):
        sign_h = _sign_of_house(asc_sign, h)
        out[str(h)] = SIGN_LORD[sign_h]
    return out

# ------------------------------------------------------------
# Jaimini: Dual lordship & Rashi Drishti helpers
# ------------------------------------------------------------

# SIGNS = ["Ar","Ta","Ge","Cn","Le","Vi","Li","Sc","Sg","Cp","Aq","Pi"]
# を前提としたモダリティ分け
MOVABLE_SIGNS = (SIGNS[0], SIGNS[3], SIGNS[6], SIGNS[9])   # Ar, Cn, Li, Cp
FIXED_SIGNS   = (SIGNS[1], SIGNS[4], SIGNS[7], SIGNS[10])  # Ta, Le, Sc, Aq
DUAL_SIGNS    = (SIGNS[2], SIGNS[5], SIGNS[8], SIGNS[11])  # Ge, Vi, Sg, Pi

# ジャイミニで吉星とみなす 3 惑星（木星・水星・金星）
BENEFIC_FOR_JAIMINI: Tuple[str, ...] = ("Ju", "Me", "Ve")

# 蠍座・水瓶座の二重支配
#   Sc: 火星 / ケートゥ
#   Aq: 土星 / ラーフ
DUAL_SIGN_LORDS: Dict[str, Tuple[str, str]] = {
    "Sc": ("Ma", "Ke"),
    "Aq": ("Sa", "Ra"),
}


def _are_adjacent_signs(sign1: str, sign2: str) -> bool:
    """
    同じ並びで隣り合うサインかどうか（ラーシ・ドリシュティの例外判定用）。
    例: Ar と Ta は隣接、Ar と Pi も隣接。
    """
    i1 = _sign_index(sign1)
    i2 = _sign_index(sign2)
    return (i1 - i2) % 12 in (1, 11)


def _jaimini_rashi_aspect(from_sign: str, to_sign: str) -> bool:
    """
    ジャイミニ・ラーシ・ドリシュティ（サイン同士）:

      - 動サイン → 不動サイン（隣接するサインは除外）
      - 不動サイン → 動サイン（隣接するサインは除外）
      - 両義サイン → 両義サイン（自室以外）

    ※惑星ではなく「サイン単位」でのアスペクト。
    """
    if from_sign == to_sign:
        return False

    if from_sign in MOVABLE_SIGNS and to_sign in FIXED_SIGNS:
        return not _are_adjacent_signs(from_sign, to_sign)

    if from_sign in FIXED_SIGNS and to_sign in MOVABLE_SIGNS:
        return not _are_adjacent_signs(from_sign, to_sign)

    if from_sign in DUAL_SIGNS and to_sign in DUAL_SIGNS:
        return True

    return False


def _planet_sign(d1: Dict, pname: str) -> Optional[str]:
    """
    惑星のサイン略号を返す。
    d1["planets"][pname]["sign"] を想定。
    """
    return d1.get("planets", {}).get(pname, {}).get("sign")


def _planet_degree_in_sign(d1: Dict, pname: str) -> float:
    """
    惑星のサイン内度数を返す（0..29.99）。

    - d1["planets"][pname]["degree"] が 0..30 未満のサイン内度数を想定
      （build_d1 による D1 出力仕様に合わせる）。
    - None / 不正値の場合は 0.0 とみなす。
    - ラーフ / ケートゥ の場合は effective_deg = 30 - degree として評価。
    """
    p = d1.get("planets", {}).get(pname, {})
    raw = p.get("degree")

    if isinstance(raw, (int, float)):
        deg = float(raw)
    else:
        deg = 0.0

    # 念のため 0..30 にクランプ
    if deg < 0.0:
        deg = 0.0
    if deg >= 30.0:
        deg = 29.99

    # Ra / Ke は effective_deg = 30 - degree
    if pname == "Ra" or pname == "Ke":
        return 30.0 - deg

    return deg


def _count_planets_in_same_sign(d1: Dict, lord_name: str) -> int:
    """
    支配星と同じサインにいる惑星の数（支配星自身は含めない）。
    """
    l_sign = _planet_sign(d1, lord_name)
    if not l_sign:
        return 0

    cnt = 0
    for pname, pdata in d1.get("planets", {}).items():
        if pname == lord_name:
            continue
        if pdata.get("sign") == l_sign:
            cnt += 1
    return cnt


def _count_benefic_jaimini_aspects_to_lord(d1: Dict, lord_name: str) -> int:
    """
    木星・水星・金星が、ジャイミニ・ラーシ・ドリシュティで
    支配星のいるサインにアスペクトしている数。
    """
    l_sign = _planet_sign(d1, lord_name)
    if not l_sign:
        return 0

    cnt = 0
    for bname in BENEFIC_FOR_JAIMINI:
        b_sign = _planet_sign(d1, bname)
        if not b_sign:
            continue
        if _jaimini_rashi_aspect(b_sign, l_sign):
            cnt += 1

    return cnt


def _score_dual_lord_strength(d1: Dict, lord_name: str) -> Tuple[int, int, float]:
    """
    二重支配星の強さスコアを返す:
      (同宮惑星数, 吉星Rashiドリシュティ数, effective_deg)

    比較優先順位:
      1) 同宮惑星数
      2) 吉星ジャイミニ・アスペクト数
      3) effective_deg（Ra/Ke は 30 - degree）
    """
    same_sign_cnt = _count_planets_in_same_sign(d1, lord_name)
    benefic_aspect_cnt = _count_benefic_jaimini_aspects_to_lord(d1, lord_name)
    eff_deg = _planet_degree_in_sign(d1, lord_name)
    return (same_sign_cnt, benefic_aspect_cnt, eff_deg)


def _choose_dual_lord_for_sign(d1: Dict, base_sign: str) -> Optional[str]:
    """
    蠍座 / 水瓶座のとき、火星/ケートゥ or 土星/ラーフ から強い方を返す。
    それ以外のサインでは None を返す（呼び出し側で無視）。

    base_sign:
      - AL の場合: Asc サイン（1室）のサイン
      - UL の場合: Asc から数えた 12 室目のサイン
    """
    cand = DUAL_SIGN_LORDS.get(base_sign)
    if not cand:
        return None

    lord1, lord2 = cand
    score1 = _score_dual_lord_strength(d1, lord1)
    score2 = _score_dual_lord_strength(d1, lord2)

    # (同宮惑星数, 吉星アスペクト数, effective_deg) でタプル比較
    if score1 >= score2:
        return lord1
    return lord2

def _arudha_for_house(d1: Dict, target_house: int) -> str:
    """
    あるハウス target_house の Arudha（Pada）サイン略号（Whole Sign）。

    一般則：
      1) H の支配星のハウス位置までの距離 d（1..12）を数える（H→支配星、順行・包含カウント）
      2) 支配星の位置から d を順行で数えた先が Arudha（Pada）
      3) 例外：最終的に得られた Pada が、
         ・H（対象ハウス）そのもの、または
         ・H から 7室目（対向）に落ちた場合、
         → その位置から 10室目を Arudha に置き換える

    追加仕様（Jaimini 二重支配 / 蠍座・水瓶座）:

      - target_house に対応するサインが Sc / Aq の場合、
        火星/ケートゥ または 土星/ラーフ のうち、
        以下の優先順位で強い方を支配星とみなして距離を数える。

          1) 支配星と同宮する惑星の数が多い方
          2) 木星・水星・金星からのジャイミニ・ラーシ・ドリシュティを多く受ける方
          3) effective_deg が大きい方（Ra/Ke は 30 - degree）

      - target_house の意味づけ:
          1 → AL: Asc サインの Arudha（Arudha Lagna）
         12 → UL: Asc から数えた 12室サインの Arudha（Upapada Lagna）
    """
    asc_sign: str = d1["Asc"]["sign"]
    planets: Dict[str, Dict] = d1.get("planets", {})
    lords: Dict[str, str] = d1.get("lords") or _lords_by_house_from_asc(asc_sign)

    # Asc を基点に target_house のサインを取得
    #   target_house = 1 → Asc サイン
    #   target_house = 12 → Asc から数えた 12室目のサイン
    base_sign = _sign_of_house(asc_sign, target_house)

    # 1) 対象ハウスのデフォルト支配星（従来の D1 ロード）
    default_lord = lords[str(target_house)]

    # 2) 蠍座 / 水瓶座なら二重支配ロジックで支配星を上書き
    dual_lord = _choose_dual_lord_for_sign(d1, base_sign)
    lord = dual_lord or default_lord

    # 3) 支配星のハウス位置（Whole Sign）
    lord_house = int(planets.get(lord, {}).get("house", 1))  # 安全策：無い場合は1室

    # 4) H→支配星 までの距離 d（1..12）
    d = _distance(target_house, lord_house)

    # 5) 支配星の位置から d を順行で数えた先が 基本の Arudha
    ar_house = ((lord_house - 1) + (d - 1)) % 12 + 1  # 1..12

    # 6) 例外：最終の Arudha が H 本人 or H から 7室目に落ちたら → その位置から 10室目へジャンプ
    opp_house = ((target_house + 6 - 1) % 12) + 1  # 7室目（+6）
    if ar_house == target_house or ar_house == opp_house:
        ar_house = ((ar_house + 9 - 1) % 12) + 1  # 10室目（+9）

    # 7) Asc サインから house番号→サイン略号に変換して返す
    return _sign_of_house(asc_sign, ar_house)

def arudha_lagna(d1: Dict) -> str:
    """AL（Arudha Lagna）"""
    return _arudha_for_house(d1, 1)

def upapada_lagna(d1: Dict) -> str:
    """UL（Upapada Lagna）…12室の Arudha"""
    return _arudha_for_house(d1, 12)