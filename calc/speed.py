# calc/speed.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional

# 速度しきい値（deg/day）。
# - station: |speed| <= station → station
# - fast:    |speed| >= fast    → fast
# - very_fast: |speed| >= very_fast → very_fast（fastより優先）
# - very_slow: |speed| <= very_slow → very_slow（stationより後に評価）
#
# retrograde は speed < 0 で独立に付与します（Sunは除外）。
#
# 注) 数値は実用上の観測レンジに基づく目安。プロジェクト方針に合わせて調整してください。

@dataclass(frozen=True)
class SpeedThreshold:
    station: Optional[float] = None
    fast: Optional[float] = None
    very_fast: Optional[float] = None
    very_slow: Optional[float] = None

# 惑星略号: Su, Mo, Ma, Me, Ju, Ve, Sa, Ra, Ke
THRESHOLDS: Dict[str, SpeedThreshold] = {
    # Moon：変動幅が大きいので very_slow/very_fast を明確化
    # 例: station≈0.3 は「月食近傍で見かけ上の停滞」を拾うための保守的設定
    "Mo": SpeedThreshold(station=0.30, fast=14.8, very_fast=15.1, very_slow=12.0),

    # Sun：station しない。fast/very_fastは観測的な揺らぎのラベル付け
    "Su": SpeedThreshold(station=None, fast=1.00, very_fast=1.10, very_slow=None),

    # 水金火木土：観測レンジからの実用的なしきい値
    "Me": SpeedThreshold(station=0.03, fast=1.60, very_fast=2.00, very_slow=None),
    "Ve": SpeedThreshold(station=0.03, fast=1.15, very_fast=1.60, very_slow=None),
    "Ma": SpeedThreshold(station=0.05, fast=0.65, very_fast=0.90, very_slow=None),
    "Ju": SpeedThreshold(station=0.03, fast=0.20, very_fast=0.25, very_slow=None),
    "Sa": SpeedThreshold(station=0.02, fast=0.11, very_fast=0.15, very_slow=None),

    # Nodes（Mean/True共通の目安）。True Nodeは正転もあり得る。
    "Ra": SpeedThreshold(station=0.01, fast=0.06, very_fast=None, very_slow=None),
    "Ke": SpeedThreshold(station=0.01, fast=0.06, very_fast=None, very_slow=None),
}

# デフォルト（未設定惑星があれば）
DEFAULT = SpeedThreshold(station=0.05, fast=None, very_fast=None, very_slow=None)

def classify_speed(planet: str, speed: float) -> str:
    """
    速度の絶対値に基づき、ラベルを返す（retrogradeは別）。
    返り値: 'station' | 'very_fast' | 'fast' | 'very_slow' | 'normal'
    """

    # --- 追加：Keは常に normal 扱い ---
    if planet == "Ke":
        return "normal"

    v = abs(float(speed))
    th = THRESHOLDS.get(planet, DEFAULT)

    # 1) station（Sunは判定しない）
    if planet != "Su" and th.station is not None and v <= th.station:
        return "station"

    # 2) very_fast > fast（上位優先）
    if th.very_fast is not None and v >= th.very_fast:
        return "very_fast"
    if th.fast is not None and v >= th.fast:
        return "fast"

    # 3) very_slow（あえて station より後に評価：超低速とstationの重複を避ける）
    if th.very_slow is not None and v <= th.very_slow:
        return "very_slow"

    return "normal"

def flags(planet: str, speed: float) -> Dict[str, bool]:
    """
    JSON用のブールフラグ（trueのみ）。
    - retrograde: speed < 0（Sunは除外）※ Ra は retrograde を抑止
    - station / very_fast / fast / very_slow: classify_speed に従う
    - Ke: 速度関連すべて抑止（空dict）
    """
    out: Dict[str, bool] = {}

    # Ketu は速度情報すべて無効
    if planet == "Ke":
        return out

    # retrograde（Sunは常順行扱い、Ra は retrograde を付けない）
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
    # --- Ke は常に normal 扱い ---
    if planet == "Ke":
        return True
    return classify_speed(planet, speed) == "normal"
