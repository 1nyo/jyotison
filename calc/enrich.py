# calc/enrich.py
from __future__ import annotations

from typing import Dict, Mapping, Any, Optional, List, Tuple, Literal, TypedDict, cast

# ------------------------------------------------------------
# base.py から占星術データを import
# ------------------------------------------------------------
from .base import (
    SIGNS,
    SIGN_LORD,
    EXALTATION_SIGN,
    DEBILITATION_SIGN,
    MOOLATRIKONA_RANGE,
    FRIENDS,
    ENEMIES,
    nakshatra_lord_by_index,
)

# ============================================================
# TypedDict（出力 JSON の構造定義）
# ============================================================

class NakshatraEntry(TypedDict, total=False):
    name: str
    pada: int
    lord: str
    percent_left: float

class PlanetEntry(TypedDict, total=False):
    sign: str
    degree: float
    house: int
    retrograde: bool
    dignity: str
    nakshatra: NakshatraEntry
    speed: Dict[str, Any]
    tithi: Dict[str, Any]

class Chart(TypedDict, total=False):
    Asc: Dict[str, Any]
    planets: Dict[str, PlanetEntry]
    derived: Dict[str, Any]


# ============================================================
# 品位（dignity）判定ロジック
# ============================================================

def dignity_of(planet: str, sign: str, din: Optional[float] = None) -> str:
    """
    品位（dignity）を一意に返す（優先順位）：
      1) exalted
      2) debilitated
      3) moolatrikona（din 必須）
      4) owned
      5) friendly / enemy / neutral
    """

    # 1) exalted
    if EXALTATION_SIGN.get(planet) == sign:
        return "exalted"

    # 2) debilitated
    if DEBILITATION_SIGN.get(planet) == sign:
        return "debilitated"

    # 3) moolatrikona
    rng = MOOLATRIKONA_RANGE.get(planet)
    if rng and din is not None:
        mt_sign, lo, hi = rng
        if sign == mt_sign and (lo <= float(din) <= hi):
            return "moolatrikona"

    # 4) owned
    if SIGN_LORD.get(sign) == planet:
        return "owned"

    # 5) friendly / enemy / neutral
    lord = SIGN_LORD.get(sign)
    if not lord:
        return "neutral"

    if lord in FRIENDS.get(planet, []):
        return "friendly"

    if lord in ENEMIES.get(planet, []):
        return "enemy"

    return "neutral"


# ============================================================
# Derived 系ユーティリティ
# ============================================================

def _dig_bala(planets_d1: Mapping[str, PlanetEntry]) -> List[str]:
    """
    ディグバラ（方向の強さ）簡略：
      Ju/Me: house 1
      Su/Ma: house 10
      Sa   : house 7
      Mo/Ve: house 4
    """
    want = {
        "Ju": 1, "Me": 1,
        "Su": 10, "Ma": 10,
        "Sa": 7,
        "Mo": 4, "Ve": 4,
    }
    out = []
    for p, h in want.items():
        rec = planets_d1.get(p)
        if rec and rec.get("house") == h:
            out.append(p)
    return out


def _vargottama(
    planets_d1: Mapping[str, PlanetEntry],
    d9: Optional[Mapping[str, Any]]
) -> List[str]:
    """
    ヴァルゴッタマ：D1 と D9 で sign が同一の惑星。
    """
    if not isinstance(d9, Mapping):
        return []
    d9pl = d9.get("planets", {})
    if not isinstance(d9pl, dict):
        return []
    out: List[str] = []
    for p, rec in planets_d1.items():
        if p in d9pl and rec.get("sign") == d9pl[p].get("sign"):
            out.append(p)
    return out


FIRE_SIGNS = {"Ar", "Le", "Sg"}
WATER_SIGNS = {"Cn", "Sc", "Pi"}

def _gandanta(abs_long: Mapping[str, float], planets_d1: Mapping[str, PlanetEntry]) -> List[str]:
    """
    ガンダーンタ判定：
      - 火のラシ（Ar, Le, Sg）の最初の 3°20'（= 30/9 度）
      - 水のラシ（Cn, Sc, Pi）の最後の 3°20'（= 30/9 度）
    判定には D1 の惑星サイン（planets_d1[p]["sign"]）と、abs_long（0..360）からの din を用いる。
    """
    out: List[str] = []
    EDGE = 30.0 / 9.0  # 3°20' ≒ 3.333°

    for p, lon in abs_long.items():
        rec = planets_d1.get(p)
        if not isinstance(rec, dict):
            continue
        sgn = rec.get("sign")
        if not isinstance(sgn, str):
            continue

        din = float(lon % 30.0)

        if sgn in FIRE_SIGNS:
            if 0.0 <= din < EDGE:
                out.append(p)

        elif sgn in WATER_SIGNS:
            if (30.0 - EDGE) < din <= 30.0:
                out.append(p)

    return out


def _lordship_to_houses(asc_sign: str) -> Dict[str, List[int]]:
    """
    D1 ハウス支配：sign -> lord を 1..12 の各ハウスに適用し、planet -> [houses] に反転。
    """
    asc_si = SIGNS.index(asc_sign)
    planet_to_houses: Dict[str, List[int]] = {p: [] for p in ["Su","Mo","Ma","Me","Ju","Ve","Sa"]}
    for h in range(1, 13):
        sign_h = SIGNS[(asc_si + (h - 1)) % 12]
        lord = SIGN_LORD[sign_h]
        if lord in planet_to_houses:
            planet_to_houses[lord].append(h)
    return planet_to_houses


def _aspects_to_signs(asc_sign: str, planets_d1: Mapping[str, PlanetEntry]) -> Dict[str, List[str]]:
    """
    特別アスペクト簡略（サイン基準）：
      - Ma: 4, 7, 8（= +3, +6, +7 サイン先）
      - Ju: 5, 7, 9（= +4, +6, +8）
      - Sa: 3, 7, 10（= +2, +6, +9）
      - その他: 7（= +6）
    ※ サイン基準で簡略。ハウス基準や R/K の 5/9 を含めたい場合は拡張可。
    """
    out: Dict[str, List[str]] = {}

    def offset_sign(si: int, n: int) -> str:
        return SIGNS[(si + n) % 12]

    for p in ["Su","Mo","Ma","Me","Ju","Ve","Sa"]:
        rec = planets_d1.get(p)
        if not rec:
            continue
        sgn = rec.get("sign")
        if not isinstance(sgn, str):
            continue
        si = SIGNS.index(sgn)

        aspects: List[str] = []
        if p == "Ma":
            for n in (3, 6, 7):
                aspects.append(offset_sign(si, n))
        elif p == "Ju":
            for n in (4, 6, 8):
                aspects.append(offset_sign(si, n))
        elif p == "Sa":
            for n in (2, 6, 9):
                aspects.append(offset_sign(si, n))
        else:
            aspects.append(offset_sign(si, 6))

        out[p] = aspects

    return out


def _occupancy_in_sign(planets_d1: Mapping[str, PlanetEntry]) -> Dict[str, List[str]]:
    """
    サインごとの占有（コンジャンクト判定のベース）。
    """
    out: Dict[str, List[str]] = {s: [] for s in SIGNS}
    for p, rec in planets_d1.items():
        s = rec.get("sign")
        if s in out:
            out[s].append(p)
    # 空のサインは削除
    return {s: pls for s, pls in out.items() if pls}


def _combust(abs_long: Mapping[str, float], planets_d1: Mapping[str, PlanetEntry]) -> List[str]:
    """
    コンバスト（燃焼）：
      Sun からの最短角距離 |Δ| が以下以内なら combust とする。
        - Mo: 12°
        - Ma: 17°
        - Me: 14°（逆行中は 12°）
        - Ju: 11°
        - Ve: 10°（逆行中は 8°）
        - Sa: 15°
      ※ Su 自身は対象外。
      ※ 逆行判定は D1 の retrograde:true を参照（Me/Ve のみで使用）。
    """
    if "Su" not in abs_long:
        return []  # Sun がない場合は判定不能のため空を返す

    su = float(abs_long["Su"])

    # 基本閾値（非逆行時）
    base_thr = {
        "Mo": 12.0,
        "Ma": 17.0,
        "Me": 14.0,
        "Ju": 11.0,
        "Ve": 10.0,
        "Sa": 15.0,
    }
    # 逆行時の上書き（Me / Ve のみ）
    retro_thr = {
        "Me": 12.0,
        "Ve": 8.0,
    }

    def shortest_sep(a: float, b: float) -> float:
        # 最短角距離（0..180）
        return abs(((a - b + 180.0) % 360.0) - 180.0)

    out: List[str] = []

    for p, lon in abs_long.items():
        if p == "Su":
            continue
        if p not in base_thr:
            continue  # 閾値未定義の惑星（Ra/Keなど）はスキップ

        # 逆行中なら逆行用閾値に置換（Me/Veのみ該当）
        thr = base_thr[p]
        rec = planets_d1.get(p, {})
        if rec.get("retrograde") is True and p in retro_thr:
            thr = retro_thr[p]

        dd = shortest_sep(float(lon), su)
        if dd <= thr:
            out.append(p)

    return out


def _planetary_war(planets_d1: Mapping[str, PlanetEntry], abs_long: Mapping[str, float]) -> List[str]:
    """
    グラハユッダ（簡略）：
      Me/Ve/Ma/Ju/Sa のうち、同サインで 1°以内に 2体以上 → 巻き込まれ惑星名を返す。
      勝敗は付けない（用途に応じて拡張可）。
    """
    candidates = ["Me","Ve","Ma","Ju","Sa"]
    out_set = set()

    # sign ごとにグループ化
    sign_groups: Dict[str, List[Tuple[str, float]]] = {}
    for p in candidates:
        rec = planets_d1.get(p)
        if rec:
            s = rec.get("sign")
            if s:
                sign_groups.setdefault(s, []).append((p, abs_long.get(p, -999.0)))

    for s, arr in sign_groups.items():
        arr = [(p, lon) for p, lon in arr if lon >= 0]
        arr.sort(key=lambda x: x[1])

        for i in range(len(arr) - 1):
            p1, l1 = arr[i]
            p2, l2 = arr[i + 1]
            if abs(l2 - l1) <= 1.0:
                out_set.add(p1)
                out_set.add(p2)

    return sorted(out_set)


# ============================================================
# enrich_d1：D1 を拡張
# ============================================================

def enrich_d1(d1: Chart, planets_raw: Dict[str, Dict], d9: Optional[Chart] = None) -> Chart:

    # 惑星の絶対黄経（0..360）
    abs_long_raw = {p: rec.get("_lon360") for p, rec in planets_raw.items() if isinstance(rec, dict)}
    abs_long: Dict[str, float] = {}
    for p, val in abs_long_raw.items():
        try:
            if val is not None:
                abs_long[p] = float(val)
        except (TypeError, ValueError):
            pass

    # --- Asc の nakshatra.lord ---
    asc = d1.get("Asc", {})
    if isinstance(asc, dict):
        nak = asc.get("nakshatra")
        if isinstance(nak, dict) and "name" in nak and "pada" in nak:
            s = asc.get("sign")
            deg = asc.get("degree")
            asc_lon = None
            if isinstance(s, str) and s in SIGNS and isinstance(deg, (int, float)):
                asc_lon = SIGNS.index(s) * 30.0 + float(deg)
            if asc_lon is not None:
                idx = int(asc_lon // (360.0 / 27.0)) % 27
                lord = nakshatra_lord_by_index(idx)
                asc["nakshatra"] = {
                    "name": nak.get("name"),
                    "pada": nak.get("pada"),
                    "lord": lord,
                }
        d1["Asc"] = asc

    # --- 惑星の nakshatra.lord ＆ dignity ---
    pls = d1.get("planets", {})

    for p, rec in pls.items():

        # (a) Nakshatra lord
        nak = rec.get("nakshatra")
        if isinstance(nak, dict) and "name" in nak and "pada" in nak:
            lon = abs_long.get(p)
            lord = None

            if lon is not None:
                idx = int(lon // (360.0 / 27.0)) % 27
                lord = nakshatra_lord_by_index(idx)

            ordered: NakshatraEntry = {}

            name_v = nak.get("name")
            if isinstance(name_v, str):
                ordered["name"] = name_v

            pada_v = nak.get("pada")
            if isinstance(pada_v, int):
                ordered["pada"] = pada_v

            if lord is not None:
                ordered["lord"] = lord
            else:
                lv = nak.get("lord")
                if isinstance(lv, str):
                    ordered["lord"] = lv

            pl = nak.get("percent_left")
            try:
                if pl is not None:
                    ordered["percent_left"] = float(pl)
            except Exception:
                pass

            rec["nakshatra"] = ordered

        # (b) dignity（Ra/Ke 以外）
        if p not in ("Ra", "Ke"):
            s = rec.get("sign")
            if isinstance(s, str):
                lon = abs_long.get(p)
                din = float(lon % 30.0) if lon is not None else None
                rec["dignity"] = dignity_of(p, s, din)

    # --- derived data ---
    derived: Dict[str, Any] = {}
    pls2 = cast(Dict[str, PlanetEntry], pls)

    derived["dig_bala"] = _dig_bala(pls2)
    derived["vargottama"] = _vargottama(pls2, d9)
    derived["gandanta"] = _gandanta(abs_long, pls2)

    asc_sign = cast(str, d1.get("Asc", {}).get("sign"))
    derived["lordship_to_houses"] = _lordship_to_houses(asc_sign)
    derived["aspects_to_sign"] = _aspects_to_signs(asc_sign, pls2)
    derived["occupancy_in_sign"] = _occupancy_in_sign(pls2)
    derived["combust"] = _combust(abs_long, pls2)
    derived["planetary_war"] = _planetary_war(pls2, abs_long)

    d1["derived"] = derived
    return d1


# ============================================================
# apply_varga_flags（D3/D4/D7/D9…に dignity を適用）
# ============================================================

def apply_varga_flags(
    varga: Chart,
    d1: Chart,
    kind: Literal["D9", "D3", "D4", "D7", "D10", "D12", "D16", "D20", "D24", "D30", "D60"]
) -> Chart:

    d1pl: Dict[str, PlanetEntry] = {}
    pl = d1.get("planets")
    if isinstance(pl, dict):
        d1pl = cast(Dict[str, PlanetEntry], pl)

    pls = varga.get("planets")
    if not isinstance(pls, dict):
        return varga

    for p, rec in pls.items():
        if not isinstance(rec, dict):
            continue

        # retrograde コピー
        if isinstance(d1pl.get(p), dict) and d1pl[p].get("retrograde") is True:
            rec["retrograde"] = True

        # Ra/Ke は dignity 無し
        if p in ("Ra", "Ke"):
            rec.pop("dignity", None)
            continue

        s = rec.get("sign")
        if not isinstance(s, str):
            rec.pop("dignity", None)
            continue

        din_raw = rec.get("degree")
        din = float(din_raw) if isinstance(din_raw, (int, float)) else None

        d = dignity_of(p, s, din)

        if kind == "D9":
            # D9 は 4 種類のみ出力
            if d in {"exalted", "debilitated", "moolatrikona", "owned"}:
                rec["dignity"] = d
            else:
                rec.pop("dignity", None)
        else:
            # 他の分割図は exalted / debilitated のみ
            if d in {"exalted", "debilitated"}:
                rec["dignity"] = d
            else:
                rec.pop("dignity", None)

    return varga


# ------------------------------------------------------------
# 公開 API
# ------------------------------------------------------------
__all__ = ["enrich_d1", "apply_varga_flags", "Chart", "PlanetEntry"]