# calc/speed.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional

"""
速度判定ユーティリティ（deg/day ベース）

責務：
  - 各惑星の観測レンジに基づき、速度のラベルを決定する
      classify_speed(planet, speed) -> 'station'|'very_fast'|'fast'|'very_slow'|'normal'
  - JSON 用のブールフラグを返す
      flags(planet, speed) -> {"retrograde": True, "station": True, ...}（true のみ）

設計方針（2026 版）:
  - retrograde は speed とは独立の boolean（Sun は除外、Ra は retrograde 抑止、Ke は速度関連すべて抑止）
  - Ke は速度ラベルも常に 'normal' 扱い（速度関連は JSON に出さない想定）
  - speed.status は classify_speed の戻り値をそのまま使う（'normal' も含む）
  - 出力 ON/OFF（speed キーの有無）はアプリ側（streamlit_app.apply_output_options）で制御する
"""

# 速度しきい値（deg/day）。
# - station:   |speed| <= station        → "station"
# - fast:      |speed| >= fast          → "fast"
# - very_fast: |speed| >= very_fast     → "very_fast"（fast より優先）
# - very_slow: |speed| <= very_slow     → "very_slow"（station より後に評価）
#
# retrograde は speed < 0 で独立に付与します（Sun は除外。Ra は retrograde を付けない）。
#
# 注) 数値は実用上の観測レンジに基づく目安。必要なら調整してください。

@dataclass(frozen=True)
class SpeedThreshold:
    station: Optional[float] = None
    fast: Optional[float] = None
    very_fast: Optional[float] = None
    very_slow: Optional[float] = None


# 惑星略号: Su, Mo, Ma, Me, Ju, Ve, Sa, Ra, Ke
THRESHOLDS: Dict[str, SpeedThreshold] = {
    # Moon：変動幅が大きいので very_slow / very_fast を明確化
    # 例: station≈0.3 は「月食近傍で見かけ上の停滞」を拾うための保守的設定
    "Mo": SpeedThreshold(station=0.30, fast=14.8, very_fast=15.1, very_slow=12.0),

    # Sun：station しない。fast/very_fast は観測的な揺らぎのラベル付け
    "Su": SpeedThreshold(station=None, fast=1.00, very_fast=1.10, very_slow=None),

    # 水金火木土：観測レンジからの実用的なしきい値
    "Me": SpeedThreshold(station=0.03, fast=1.60, very_fast=2.00, very_slow=None),
    "Ve": SpeedThreshold(station=0.03, fast=1.15, very_fast=1.60, very_slow=None),
    "Ma": SpeedThreshold(station=0.05, fast=0.65, very_fast=0.90, very_slow=None),
    "Ju": SpeedThreshold(station=0.03, fast=0.20, very_fast=0.25, very_slow=None),
    "Sa": SpeedThreshold(station=0.02, fast=0.11, very_fast=0.15, very_slow=None),

    # Nodes（Mean/True 共通の目安）。True Node は正転もあり得る。
    "Ra": SpeedThreshold(station=0.01, fast=0.06, very_fast=None, very_slow=None),
    "Ke": SpeedThreshold(station=0.01, fast=0.06, very_fast=None, very_slow=None),
}

# デフォルト（しきい値未定義の惑星用）
DEFAULT = SpeedThreshold(station=0.05, fast=None, very_fast=None, very_slow=None)


def classify_speed(planet: str, speed: float) -> str:
    """
    速度の絶対値に基づきラベルを返す（retrograde は別処理）。
    戻り値: 'station' | 'very_fast' | 'fast' | 'very_slow' | 'normal'
    """

    # Ketu は速度情報を特別扱い（常に normal）
    if planet == "Ke":
        return "normal"

    v = abs(float(speed))
    th = THRESHOLDS.get(planet, DEFAULT)

    # 1) station（Sun は station 判定しない）
    if planet != "Su" and th.station is not None and v <= th.station:
        return "station"

    # 2) very_fast > fast（上位優先）
    if th.very_fast is not None and v >= th.very_fast:
        return "very_fast"
    if th.fast is not None and v >= th.fast:
        return "fast"

    # 3) very_slow（station との重複を避けるため、あえて station 判定の後に評価）
    if th.very_slow is not None and v <= th.very_slow:
        return "very_slow"

    return "normal"


def flags(planet: str, speed: float) -> Dict[str, bool]:
    """
    JSON 用のブールフラグ（true のみ返す）。

    - 'retrograde': speed < 0（Sun は除外、Ra は retrograde を付けない）
    - 'station' / 'very_fast' / 'fast' / 'very_slow': classify_speed に従う
    - Ke: 速度関連すべて抑止（空 dict を返す）
    """
    out: Dict[str, bool] = {}

    # Ketu は速度情報すべて無効
    if planet == "Ke":
        return out

    # retrograde（Sun は常順行扱い、Ra は retrograde を付けない）
    if planet not in ("Su", "Ra") and speed < 0:
        out["retrograde"] = True

    label = classify_speed(planet, speed)
    if label == "station":
        out["station"] = True
    elif label == "very_fast":
        out["very_fast"] = True
    elif label == "fast":
        out["fast"] = True
    elif label == "very_slow":
        out["very_slow"] = True

    return out


def is_normal_speed(planet: str, speed: float) -> bool:
    """
    classify_speed のラッパー。
    互換性維持用（他所で使っていればそのまま動く）。
    """
    if planet == "Ke":
        return True
    return classify_speed(planet, speed) == "normal"
