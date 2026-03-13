# calc/enrich.py
from __future__ import annotations

from typing import Dict, Mapping, Any, Optional, List, Tuple, Literal, TypedDict, cast
from .base import SIGNS, SIGN_LORD, EXALTATION_SIGN

from typing import Dict, Mapping, Any, Optional, List, Tuple, Literal, TypedDict, cast

# 追加：nakshatra 用の TypedDict（D1/Mo の percent_left を許容）
class NakshatraEntry(TypedDict, total=False):
    name: str
    pada: int
    lord: str
    percent_left: float

# 既存の PlanetEntry を拡張
class PlanetEntry(TypedDict, total=False):
    sign: str
    degree: float
    house: int
    retrograde: bool
    dignity: str
    nakshatra: NakshatraEntry   # ★ これで rec["nakshatra"] 代入が合法に
    speed: Dict[str, Any]       # status/value など（柔らかくしておく）
    tithi: Dict[str, Any]       # Moon 用（name/paksha/percent_left 等）

# Chart に derived を追加（optional）
class Chart(TypedDict, total=False):
    Asc: Dict[str, Any]
    planets: Dict[str, PlanetEntry]
    derived: Dict[str, Any]

# ============================================================
# 1) ナクシャトラ支配星（略号）
#    伝統順列（Ashwini→Ketu, Bharani→Venus, Krittika→Sun, ...）
# ============================================================

_NAK_LORD_SEQ = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
# 27座 = 9の繰り返し ×3
NAK_LORDS: List[str] = (_NAK_LORD_SEQ * 3)[:27]

def nakshatra_lord_by_index(idx: int) -> str:
    return NAK_LORDS[idx % 27]


# ============================================================
# 2) 自然友好表（classical）— 流派差あり・必要に応じて調整可
# ============================================================

FRIENDS: Dict[str, List[str]] = {
    "Su": ["Mo", "Ma", "Ju"],
    "Mo": ["Su", "Me"],
    "Ma": ["Su", "Mo", "Ju"],
    "Me": ["Su", "Ve"],
    "Ju": ["Su", "Mo", "Ma"],
    "Ve": ["Me", "Sa"],
    "Sa": ["Me", "Ve"],
    "Ra": [],  # ノードは中立扱い
    "Ke": [],
}

ENEMIES: Dict[str, List[str]] = {
    "Su": ["Ve", "Sa"],
    "Mo": [],              # 明確な敵なし → 中立寄り
    "Ma": ["Me"],
    "Me": ["Mo"],
    "Ju": ["Me", "Ve"],
    "Ve": ["Su", "Mo"],
    "Sa": ["Su", "Mo","Ma"],
    "Ra": [],
    "Ke": [],
}


# ============================================================
# 3) 減衰（debilitation）サイン：高揚サインの対向 / MTレンジ
# ============================================================

DEBILITATION_SIGN: Dict[str, str] = {p: SIGNS[(SIGNS.index(s) + 6) % 12] for p, s in EXALTATION_SIGN.items()}

# Moolatrikona のサイン＆度数レンジ（サイン内度数：両端含む）
# 伝統的な代表値に準拠：Sun(Le 0-20), Moon(Ta 3-30), Mars(Ar 0-12),
# Mercury(Vi 15-20), Jupiter(Sg 0-10), Venus(Li 0-15), Saturn(Aq 0-20)
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

def dignity_of(planet: str, sign: str, din: Optional[float] = None) -> str:
    """
    一意の 品位（dignity）を返す（優先順）：
      1) exalted
      2) debilitated
      3) moolatrikona（din=サイン内度数が必要）
      4) owned（自室）
      5) friendly / enemy / neutral（自然友好表、sign のローダー基準）
    """
    # 1) exalted
    if EXALTATION_SIGN.get(planet) == sign:
        return "exalted"

    # 2) debilitated
    if DEBILITATION_SIGN.get(planet) == sign:
        return "debilitated"

    # 3) moolatrikona（din があれば判定）
    rng = MOOLATRIKONA_RANGE.get(planet)
    if rng and din is not None:
        mt_sign, lo, hi = rng
        if sign == mt_sign and (lo <= float(din) <= hi):
            return "moolatrikona"

    # 4) owned（自室）
    if SIGN_LORD.get(sign) == planet:
        return "owned"

    # 5) 友敵（自然関係）
    lord = SIGN_LORD.get(sign)
    if not lord:
        return "neutral"
    if lord in FRIENDS.get(planet, []):
        return "friendly"
    if lord in ENEMIES.get(planet, []):
        return "enemy"
    return "neutral"


# ============================================================
# 4) 付帯：Derived系のユーティリティ
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

def _vargottama(planets_d1: Mapping[str, PlanetEntry], d9: Optional[Mapping[str, Any]]) -> List[str]:
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
      - 火のラシ（Ar, Le, Sg）の最初の 3°20′（= 30/9 度）
      - 水のラシ（Cn, Sc, Pi）の最後の 3°20′（= 30/9 度）
    判定には D1 の惑星サイン（planets_d1[p]["sign"]）と、abs_long（0..360）からの din を用いる。
    """
    out: List[str] = []
    EDGE = 30.0 / 9.0  # 3°20′ = 3.333...°

    for p, lon in abs_long.items():
        rec = planets_d1.get(p)
        if not isinstance(rec, dict):
            continue
        sgn = rec.get("sign")
        if not isinstance(sgn, str):
            continue

        din = float(lon % 30.0)  # 0..30
        if sgn in FIRE_SIGNS:
            if din >= 0.0 and din < EDGE:
                out.append(p)
        elif sgn in WATER_SIGNS:
            if din > (30.0 - EDGE) and din <= 30.0:
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
      - Ma: 4, 7, 8（＝+3, +6, +7 サイン先）
      - Ju: 5, 7, 9（＝+4, +6, +8）
      - Sa: 3, 7, 10（＝+2, +6, +9）
      - その他: 7（＝+6）
    ※ サイン基準で簡略。ハウス基準や R/K の 5/9 を含めたい場合は拡張可。
    """
    out: Dict[str, List[str]] = {}

    def offset_sign(si: int, n: int) -> str:
        return SIGNS[(si + n) % 12]

    for p in ["Su","Mo","Ma","Me","Ju","Ve","Sa"]:
        rec = planets_d1.get(p)
        if not rec:
            continue
        sgn = rec.get("sign")            # ★ ここを get に
        if not isinstance(sgn, str):     # ★ ガード
            continue
        si = SIGNS.index(sgn)            # ★ これで警告が消える
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

def _combust(planets_abs: Mapping[str, float], planets_d1: Mapping[str, PlanetEntry]) -> List[str]:
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
    if "Su" not in planets_abs:
        return []  # Sun がない場合は判定不能のため空

    su = float(planets_abs["Su"])

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
    for p, lon in planets_abs.items():
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

def _planetary_war(planets_d1: Mapping[str, PlanetEntry], planets_abs: Mapping[str, float]) -> List[str]:
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
                sign_groups.setdefault(s, []).append((p, planets_abs.get(p, -999.0)))

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
# 5) 外部 API
# ============================================================

def enrich_d1(d1: Chart, planets_raw: Dict[str, Dict], d9: Optional[Chart] = None) -> Chart:
    """
    D1 の各惑星・Asc・derived を拡張して返す。
      - Asc.nakshatra.lord を追加（name, pada, lord のみ。percent_left は付けない）
      - planets.*.nakshatra.lord を追加（name, pada, lord[, percent_left]）
      - planets.*.dignity を追加（exalted/debilitated/moolatrikona/owned/friendly/enemy/neutral）
      - derived を合成（dig_bala, vargottama, gandanta, lordship_to_houses,
        occupancy_in_sign, combust, planetary_war ほか）
    """
    # 0) 惑星の絶対黄経（0..360）— float のみに正規化
    abs_long_raw = {p: rec.get("_lon360") for p, rec in planets_raw.items() if isinstance(rec, dict)}
    abs_long: Dict[str, float] = {}
    for p, val in abs_long_raw.items():
        try:
            if val is None:
                continue
            abs_long[p] = float(val)
        except (TypeError, ValueError):
            pass

    # --- Asc の nakshatra.lord（name, pada, lord のみ） ---
    asc = d1.get("Asc", {})
    if isinstance(asc, dict):
        nak = asc.get("nakshatra")
        if isinstance(nak, dict) and "name" in nak and "pada" in nak:
            s = asc.get("sign"); deg = asc.get("degree")
            asc_lon = None
            if isinstance(s, str) and s in SIGNS and isinstance(deg, (int, float)):
                asc_lon = SIGNS.index(s) * 30.0 + float(deg)
            if asc_lon is not None:
                idx = int(asc_lon // (360.0 / 27.0)) % 27
                lord = nakshatra_lord_by_index(idx)
                asc["nakshatra"] = {"name": nak.get("name"), "pada": nak.get("pada"), "lord": lord}
        d1["Asc"] = asc

    # 1) 惑星：nakshatra.lord / dignity
    pls = d1.get("planets", {})
    for p, rec in pls.items():
        # (a) nakshatra.lord（name, pada, lord[, percent_left]）
        nak = rec.get("nakshatra")
        if isinstance(nak, dict) and "name" in nak and "pada" in nak:
            lon = abs_long.get(p); lord = None
            if lon is not None:
                idx = int(lon // (360.0 / 27.0)) % 27
                lord = nakshatra_lord_by_index(idx)

            # ★ 段階的に NakshatraEntry を構築（None を排除）
            ordered_nak: NakshatraEntry = {}

            name_v = nak.get("name")
            if isinstance(name_v, str):
                ordered_nak["name"] = name_v

            pada_v = nak.get("pada")
            if isinstance(pada_v, int):
                ordered_nak["pada"] = pada_v

            if lord is not None:
                ordered_nak["lord"] = lord
            else:
                lord_v = nak.get("lord")
                if isinstance(lord_v, str):
                    ordered_nak["lord"] = lord_v

            pl = nak.get("percent_left")
            try:
                if pl is not None:
                    ordered_nak["percent_left"] = float(pl)
            except (TypeError, ValueError):
                pass

            rec["nakshatra"] = ordered_nak

        # (b) dignity（Ra/Ke は付与しない）
        if p not in ("Ra", "Ke"):
            s = rec.get("sign")
            if isinstance(s, str):
                lon = abs_long.get(p)
                din = float(lon % 30.0) if lon is not None else None
                rec["dignity"] = dignity_of(p, s, din)

    # 2) derived
    derived: Dict[str, Any] = {}
    pls = cast(Dict[str, PlanetEntry], d1.get("planets", {}))  # ★ PlanetEntry として具体化

    derived["dig_bala"] = _dig_bala(pls)
    derived["vargottama"] = _vargottama(pls, d9)
    derived["gandanta"] = _gandanta(abs_long, pls)

    # Asc.sign の型を具体化（警告回避）
    asc_sign = cast(str, d1.get("Asc", {}).get("sign"))

    derived["lordship_to_houses"] = _lordship_to_houses(asc_sign)
    derived["aspects_to_sign"] = _aspects_to_signs(asc_sign, pls)
    derived["occupancy_in_sign"] = _occupancy_in_sign(pls)
    derived["combust"] = _combust(abs_long, pls)
    derived["planetary_war"] = _planetary_war(pls, abs_long)

    d1["derived"] = derived
    return d1

def apply_varga_flags(varga: Chart, d1: Chart, kind: Literal["D9","D20","D60"]) -> Chart:
    """
    各分割図の惑星に対し、
      - retrograde: D1 の状態をコピー
      - dignity:
          * D9: exalted / debilitated / moolatrikona / owned（Ra/Ke は常に除外）
          * D20/D60: exalted / debilitated（Ra/Ke は常に除外）
    """
    # d1["planets"] を安全に取り出す（存在チェック＋型キャスト）
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

        # retrograde コピー（型が具体化され補完も効きます）
        if isinstance(d1pl.get(p), dict) and d1pl[p].get("retrograde") is True:
            rec["retrograde"] = True

        # Ra/Ke は dignity 抑止（D9 も含む）
        if p in ("Ra", "Ke"):
            rec.pop("dignity", None)
            continue

        s = rec.get("sign")
        if not isinstance(s, str):
            continue

        if kind == "D9":
            din = rec.get("degree")
            dinf = float(din) if isinstance(din, (int, float)) else None
            d = dignity_of(p, s, dinf)
            if d in {"exalted", "debilitated", "moolatrikona", "owned"}:
                rec["dignity"] = d
            else:
                rec.pop("dignity", None)
        else:
            if EXALTATION_SIGN.get(p) == s:
                rec["dignity"] = "exalted"
            elif DEBILITATION_SIGN.get(p) == s:
                rec["dignity"] = "debilitated"
            else:
                rec.pop("dignity", None)

    return varga

__all__ = ["enrich_d1", "apply_varga_flags", "Chart", "PlanetEntry"]
