# calc/validators.py
from __future__ import annotations
import json
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
    - 通常の dict は改行＋インデント。
    - 通常の list は 1行。
    - ただし dasha の以下キーだけは、配列を複数行で表示（各要素は1行 or 再帰構造）：
        - dasha.full_sequence_maha
        - dasha.current_context.current_sequence （MDブロック配列）
        - dasha.current_context.current_sequence[*].antar （各MD内のAD配列）
        - （旧形式を併用している場合）dasha.current_context.antar_sequence も対象
    - さらに、複数行配列の各要素が dict の場合でも、
        * その dict の値に 'YYYY-MM-DD' が含まれていれば、その dict は 1行で出力する
          （例：{"lord":"Sa","start":"2025-02-18","label":"current"} は1行）
    """

    # dasha配下で複数行にしたい配列キー
    SPECIAL_LIST_KEYS = {"full_sequence_maha", "current_sequence", "antar", "antar_sequence"}

    # yyyy-mm-dd 判定用
    DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    def dict_contains_dateish(d: Dict[str, Any]) -> bool:
        """dict の値のいずれかが 'YYYY-MM-DD' に合致すれば True"""
        for v in d.values():
            if isinstance(v, str) and DATE_RE.match(v):
                return True
        return False

    def dump_list_one_line(lst: List[Any]) -> str:
        # 通常の配列は 1 行
        return json.dumps(lst, ensure_ascii=False, separators=(",", ":"))

    def dump_list_multiline(lst: List[Any], level: int, *, inside_dasha: bool) -> str:
        """
        配列を複数行で出力：
          - 要素が dict の場合:
              * 値に 'YYYY-MM-DD' を含む → 1行JSON に潰す（読みやすさのため）
              * 含まない → 再帰的に dump_dict（中の配列も複数行整形の対象）
          - 要素が非 dict の場合 → 1行JSON
        例：
          [
            {"lord":"Sa","start":"2025-..","end":".."},      ← 値に日付 → 1行
            { "maha_lord":"Sa",
              "antar":[ ... 複数行 ... ]                    ← 再帰整形
            }
          ]
        """
        if not lst:
            return "[]"
        pad  = " " * (indent * level)
        pad2 = " " * (indent * (level + 1))
        lines = []
        for item in lst:
            if isinstance(item, dict):
                if dict_contains_dateish(item):
                    s = json.dumps(item, ensure_ascii=False, separators=(",", ":"))
                else:
                    s = dump_dict(item, level + 1, inside_dasha=inside_dasha)
            else:
                s = json.dumps(item, ensure_ascii=False, separators=(",", ":"))
            lines.append(f"{pad2}{s}")
        return "[\n" + ",\n".join(lines) + f"\n{pad}]"

    def dump_value(v: Any, level: int, parent_key: str = "", *, inside_dasha: bool = False) -> str:
        if isinstance(v, dict):
            return dump_dict(v, level, inside_dasha=inside_dasha)
        elif isinstance(v, list):
            # dasha 配下 かつ 対象キー のときだけ配列を複数行へ
            if inside_dasha and parent_key in SPECIAL_LIST_KEYS:
                return dump_list_multiline(v, level, inside_dasha=inside_dasha)
            return dump_list_one_line(v)
        else:
            return json.dumps(v, ensure_ascii=False, separators=(",", ":"))

    def dump_dict(d: dict, level: int, *, inside_dasha: bool) -> str:
        if not d:
            return "{}"
        pad  = " " * (indent * level)
        pad2 = " " * (indent * (level + 1))
        parts = []
        for k, v in d.items():
            key = json.dumps(k, ensure_ascii=False)
            # 「dasha」キーに入ったら、その配下は inside_dasha=True を伝播
            next_inside_dasha = inside_dasha or (k == "dasha")
            parts.append(f"{pad2}{key}: {dump_value(v, level + 1, parent_key=k, inside_dasha=next_inside_dasha)}")
        return "{\n" + ",\n".join(parts) + f"\n{pad}" + "}"

    # ルート（dict想定）
    if isinstance(obj, dict):
        return dump_dict(obj, 0, inside_dasha=False)
    elif isinstance(obj, list):
        # 念のため：トップレベルが配列でも1行
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

def _validate_chart_D20_or_D60(d: dict) -> dict:
    """
    D20/D60 検証：
    - 通常 degree は持たない前提なので house のみ検証。
    - （万一 degree があっても黙って通す or 必要に応じて抑制）
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
    charts 連想（{"D1": {...}, "D9": {...}, ...}）を検証し、
    空チャートは削除して返す。
    """
    out: Dict[str, dict] = {}
    for name, chart in list(charts.items()):
        if not isinstance(chart, dict):
            continue

        # チャート別検証
        if name == "D1":
            chart = _validate_chart_D1(chart)
        elif name == "D9":
            chart = _validate_chart_D9(chart)
        elif name in ("D10", "D20", "D60"):
            chart = _validate_chart_D20_or_D60(chart)
        else:
            # 未知の図は形式のみ軽く通し、空なら捨てる
            pass

        # 空なら残さない
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

    # 旧仕様の名残（トップレベルに D1/D9/D20/D60 を生やしてしまう実装）を排除
    for k in ("D1", "D9", "D20", "D60"):
        if k in out:
            v = out.get(k)
            # charts 側に中身があるなら捨て、そうでなければ何もせず除去
            out.pop(k, None)

    # charts 配下の検証
    charts = out.get("charts", {})
    if not isinstance(charts, dict):
        charts = {}
    charts = _validate_charts(charts)

    # 反映
    out["charts"] = charts

    return out
