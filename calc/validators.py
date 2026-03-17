# calc/validators.py
from __future__ import annotations
import json
import re
from typing import Any, Dict, List, Optional

# ------------------------------
# 基本トリム
# ------------------------------
def prune_bools(d: Dict) -> Dict:
    """
    false や None は出力しない（true のみ残す）。
    dict/list は再帰的に処理。その他の値はそのまま返す。
    """
    def _pr(x: Any) -> Any:
        if isinstance(x, dict):
            return {k: _pr(v) for k, v in x.items() if v is not None and v is not False}
        elif isinstance(x, list):
            return [_pr(v) for v in x if v is not None and v is not False]
        else:
            return x
    return _pr(d)

# ------------------------------
# 単項目バリデーション
# ------------------------------
def validate_house(v: Any) -> int:
    iv = int(v)
    if not (1 <= iv <= 12):
        raise ValueError(f"house out of range: {v}")
    return iv

def validate_degree_0_30(v: Any) -> float:
    """
    度数（0.00..29.99）。小数2桁に丸め、範囲外なら例外。
    D1/D9 の degree 検証に使用。
    """
    vv = round(float(v), 2)
    if vv < 0.0 or vv >= 30.0:
        raise ValueError(f"degree out of range (0..29.99): {vv}")
    return vv

def validate_speed_value(v: Any) -> float:
    """
    速度（deg/day）：小数3桁に丸め。
    """
    return round(float(v), 3)

# ------------------------------
# 整形出力（プレビュー用）
# ------------------------------
import json
import re
from typing import Any, Dict, List

def pretty_json_inline_lists(obj: Dict, indent: int = 2) -> str:
    """
    JSON を人間向けに整形するプリティプリンタ。

    特別仕様：
    ----------------------------------------------------------
    ◆ charts.D3〜D60 の
        - Asc
        - planets.*（各惑星）
       の dict を 1 行 JSON にまとめる（compact）

    ◆ 上記以外の dict は従来どおり multi-line

    ◆ dasha 配下は従来の multi-line / inline ルールを維持
    ----------------------------------------------------------
    """

    # dasha 配下で複数行にしたい配列キー
    SPECIAL_LIST_KEYS = {
        "full_sequence_maha",
        "current_sequence",
        "antar",
        "antar_sequence",
    }

    # yyyy-mm-dd 判定用
    DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    # charts で 1 行にまとめたい Varga
    TARGET_VARGAS = {
        "D3", "D4", "D7", "D10", "D12", "D16",
        "D20", "D24", "D30", "D60",
    }

    def dict_contains_dateish(d: Dict[str, Any]) -> bool:
        for v in d.values():
            if isinstance(v, str) and DATE_RE.match(v):
                return True
        return False

    # ----------------------------------------------------------
    # charts.D3〜D60 の Asc / planets.* 判定
    # ----------------------------------------------------------
    def is_compact_varga_dict(path: List[str], value: Any) -> bool:
        """
        charts.D3〜D60 の:
          - Asc（charts.D3.Asc）
          - planets.Su, planets.Mo ...（charts.D3.planets.Su）
        の dict を 1 行に潰すかどうか判定。
        """
        if not isinstance(value, dict):
            return False
        if len(path) < 3:
            return False

        # ["charts", "D3", "Asc"] や ["charts", "D3", "planets", "Su"] を想定
        if path[0] != "charts":
            return False

        varga = path[1]
        if varga not in TARGET_VARGAS:
            return False

        # charts.D3.Asc
        if len(path) == 3 and path[2] == "Asc":
            return True

        # charts.D3.planets.Su
        if len(path) == 4 and path[2] == "planets":
            planet_key = path[3]
            if isinstance(planet_key, str) and planet_key.isalpha() and 1 <= len(planet_key) <= 3:
                return True

        return False

    # ----------------------------------------------------------
    # 以下、path-aware な pretty printer 本体
    # ----------------------------------------------------------
    def dump_list_one_line(lst: List[Any]) -> str:
        return json.dumps(lst, ensure_ascii=False)

    def dump_list_multiline(
        lst: List[Any],
        level: int,
        *,
        inside_dasha: bool,
        path: List[str],
    ) -> str:
        if not lst:
            return "[]"
        pad = " " * (indent * level)
        pad2 = " " * (indent * (level + 1))
        lines = []
        for item in lst:
            if isinstance(item, dict):
                if dict_contains_dateish(item):
                    s = json.dumps(item, ensure_ascii=False, separators=(",", ":"))
                else:
                    # 配列の中の dict → path に "*" を追加して再帰
                    s = dump_dict(item, level + 1, inside_dasha=inside_dasha, path=path + ["*"])
            else:
                s = json.dumps(item, ensure_ascii=False, separators=(",", ":"))
            lines.append(f"{pad2}{s}")
        return "[\n" + ",\n".join(lines) + f"\n{pad}]"

    def dump_value(
        v: Any,
        level: int,
        *,
        inside_dasha: bool,
        path: List[str],
    ) -> str:
        # dict
        if isinstance(v, dict):
            # charts.D3〜D60 の Asc / planets.* は 1 行にまとめる
            if is_compact_varga_dict(path, v):
                return json.dumps(v, ensure_ascii=False, separators=(",", ":"))
            return dump_dict(v, level, inside_dasha=inside_dasha, path=path)

        # list
        elif isinstance(v, list):
            # dasha 配下かつ SPECIAL_LIST_KEYS のときだけ multi-line
            if inside_dasha and path and path[-1] in SPECIAL_LIST_KEYS:
                return dump_list_multiline(v, level, inside_dasha=inside_dasha, path=path)
            return dump_list_one_line(v)

        # その他（文字列・数値など）
        else:
            return json.dumps(v, ensure_ascii=False, separators=(",", ":"))

    def dump_dict(
        d: dict,
        level: int,
        *,
        inside_dasha: bool,
        path: List[str],
    ) -> str:
        if not d:
            return "{}"
        pad = " " * (indent * level)
        pad2 = " " * (indent * (level + 1))
        parts = []
        for k, v in d.items():
            key_str = json.dumps(k, ensure_ascii=False)
            next_inside = inside_dasha or (k == "dasha")
            full_path = path + [k]  # ← このキーまでのフルパス
            val_str = dump_value(
                v,
                level + 1,
                inside_dasha=next_inside,
                path=full_path,
            )
            parts.append(f"{pad2}{key_str}: {val_str}")
        return "{\n" + ",\n".join(parts) + f"\n{pad}}}"

    # ----------------------------------------------------------
    # ルート
    # ----------------------------------------------------------
    if isinstance(obj, dict):
        return dump_dict(obj, 0, inside_dasha=False, path=[])
    elif isinstance(obj, list):
        return dump_list_one_line(obj)
    else:
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))

# ------------------------------
# チャート検証ユーティリティ
# ------------------------------
def _is_nonempty_chart(chart: Optional[dict]) -> bool:
    """
    図オブジェクトが空でないか判定：
    - dict である
    - Asc or planets のどちらかに有意な中身がある
    """
    if not isinstance(chart, dict):
        return False
    asc_ok = isinstance(chart.get("Asc"), dict) and len(chart["Asc"]) > 0
    pl_ok = isinstance(chart.get("planets"), dict) and len(chart["planets"]) > 0
    return asc_ok or pl_ok

def _validate_chart_D1(d: dict) -> dict:
    """
    D1（Rāśi）検証：
    - Asc: degree（0..30未満）
    - planets.*: degree（0..30未満）, house（1..12）, speed.value（3桁丸め）
    - retrograde は bool として残す（true のみ残るのは prune_bools に準拠）
    """
    # Asc
    if isinstance(d.get("Asc"), dict) and "degree" in d["Asc"]:
        d["Asc"]["degree"] = validate_degree_0_30(d["Asc"]["degree"])

    # planets
    if isinstance(d.get("planets"), dict):
        for p, rec in list(d["planets"].items()):
            if not isinstance(rec, dict):
                # 不正形は削除
                d["planets"].pop(p, None)
                continue
            if "house" in rec:
                rec["house"] = validate_house(rec["house"])
            if "degree" in rec:
                rec["degree"] = validate_degree_0_30(rec["degree"])
            # speed: {"value":..., "status":...} の value のみ丸め
            if "speed" in rec and isinstance(rec["speed"], dict):
                v = rec["speed"].get("value", None)
                if v is not None:
                    rec["speed"]["value"] = validate_speed_value(v)
    return d

def _validate_chart_D9(d: dict) -> dict:
    """
    D9（Navamsa）検証：
    - Asc: degree（0..30未満）
    - planets.*: degree（0..30未満）, house（1..12）
    """
    if isinstance(d.get("Asc"), dict) and "degree" in d["Asc"]:
        d["Asc"]["degree"] = validate_degree_0_30(d["Asc"]["degree"])
    if isinstance(d.get("planets"), dict):
        for p, rec in list(d["planets"].items()):
            if not isinstance(rec, dict):
                d["planets"].pop(p, None)
                continue
            if "house" in rec:
                rec["house"] = validate_house(rec["house"])
            if "degree" in rec:
                rec["degree"] = validate_degree_0_30(rec["degree"])
    return d

def _validate_chart_varga_generic(d: dict) -> dict:
    """
    D3, D4, D7, D10, D12, D16, D20, D24, D30, D60 （すべて共通）
    - degree は検証しない（存在しても黙認）
    - house だけを検証する
    """
    if isinstance(d.get("planets"), dict):
        for p, rec in list(d["planets"].items()):
            if not isinstance(rec, dict):
                d["planets"].pop(p, None)
                continue
            if "house" in rec:
                rec["house"] = validate_house(rec["house"])
    return d

def _validate_charts(charts: dict) -> dict:
    """
    charts 連想（{"D1": {...}, "D9": {...}, ...}）を検証し、空チャートを削除。
    """

    GENERIC_VARGAS = {
        "D3", "D4", "D7", "D10", "D12",
        "D16", "D20", "D24", "D30", "D60"
    }

    out: Dict[str, dict] = {}

    for name, chart in list(charts.items()):
        if not isinstance(chart, dict):
            continue

        # ---- 分割図ごとの検証 ----
        if name == "D1":
            chart = _validate_chart_D1(chart)

        elif name == "D9":
            chart = _validate_chart_D9(chart)

        elif name in GENERIC_VARGAS:
            chart = _validate_chart_varga_generic(chart)

        # ---- 空チャートは削除 ----
        if _is_nonempty_chart(chart):
            out[name] = chart

    return out

# ------------------------------
# メイン：全体の prune + validate
# ------------------------------
def prune_and_validate(out: Dict) -> Dict:
    """
    新仕様：
      - トップレベルは必ず {"schema", "generator", "birth_data", "calculation_settings", "charts"} 構造
      - charts 配下の D1/D9/D20/D60 を検証・丸め
      - 空チャートは削除
      - 旧仕様の名残（トップレベル直下に "D1": {} 等が生える）の除去
    """
    out = prune_bools(out)

    # 旧仕様の名残を削除（トップレベルに Dチャートが出てしまうバグの除去）
    ALL_VARGAS = {
        "D1", "D3", "D4", "D7", "D9", "D10", "D12",
        "D16", "D20", "D24", "D30", "D60"
    }
    for k in ALL_VARGAS:
        if k in out:
            out.pop(k, None)

    # charts 配下の検証
    charts = out.get("charts", {})
    if not isinstance(charts, dict):
        charts = {}
    charts = _validate_charts(charts)

    # 反映
    out["charts"] = charts

    return out
