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
    依存:
      - d1["Asc"]["sign"] : Ascサイン略号
      - d1["planets"][planet]["house"] : 惑星のハウス番号（1..12）
      - d1["lords"]（無ければ Asc から補完生成）
    """
    asc_sign: str = d1["Asc"]["sign"]
    planets: Dict[str, Dict] = d1.get("planets", {})
    lords: Dict[str, str] = d1.get("lords") or _lords_by_house_from_asc(asc_sign)

    # 1) 対象ハウスの支配星・その位置
    lord = lords[str(target_house)]
    lord_house = int(planets.get(lord, {}).get("house", 1))  # 安全策：無い場合は1室

    # 2) H→支配星 までの距離 d（1..12）
    d = _distance(target_house, lord_house)

    # 3) 支配星の位置から d を順行で数えた先が 基本の Arudha
    ar_house = ((lord_house - 1) + (d - 1)) % 12 + 1  # 1..12

    # 4) 例外：最終の Arudha が H 本人 or H から 7室目に落ちたら → その位置から 10室目へジャンプ
    #    ・H 自身:        ar_house == target_house
    #    ・H の 7室目:    ar_house == ((target_house + 5 - 1) % 12) + 1
    opp_house = ((target_house + 6 - 1) % 12) + 1  # 7室目（+6）
    if ar_house == target_house or ar_house == opp_house:
        ar_house = ((ar_house + 9 - 1) % 12) + 1  # 10室目（+9）

    # 5) Asc サインから house番号→サイン略号に変換して返す
    return _sign_of_house(asc_sign, ar_house)

def arudha_lagna(d1: Dict) -> str:
    """AL（Arudha Lagna）"""
    return _arudha_for_house(d1, 1)

def upapada_lagna(d1: Dict) -> str:
    """UL（Upapada Lagna）…12室の Arudha"""
    return _arudha_for_house(d1, 12)