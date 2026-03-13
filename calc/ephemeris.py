# calc/ephemeris.py
import swisseph as swe
from typing import Dict, Literal, Tuple, Optional

from .base import sign_abbr_of, deg_in_sign, fmt_deg_2, fmt_speed_3, nakshatra_of

NodeType = Literal["Mean", "True"]


def init_sidereal_lahiri(ephe_path: Optional[str] = None, jd_ut: Optional[float] = None) -> str:
    """
    Lahiri sidereal を設定し、指定時刻 jd_ut のアヤナーンシャを
    正のDMS文字列（例: '23:34:01'）で返す。
    - ephe_path: Swiss Ephemeris のデータパス（任意）
    - jd_ut: 出生等の UT JD。None の場合は J2000 の JD を用いる（後方互換）。
    """
    if ephe_path:
        swe.set_ephe_path(ephe_path)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    aya_deg = swe.get_ayanamsa_ut(jd_ut) if jd_ut is not None else swe.get_ayanamsa_ut(2451545.0)
    return dms_str_pos(float(aya_deg))


def get_ayanamsa_str_deg(jd_ut: float) -> Tuple[str, float]:
    """
    指定した UT JD における Lahiri Ayanamsa を
    - 表示用 DMS 文字列（例: '23:34:01'）
    - 数値（度、小数。例: 23.5669）
    のタプルで返す。
    事前に set_sid_mode(SIDM_LAHIRI) を呼んでいなくてもここで設定する。
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    aya = float(swe.get_ayanamsa_ut(jd_ut))
    return dms_str_pos(aya), aya


def dms_str_pos(deg: float) -> str:
    """
    23:34:01 のように正のDMSに整形（秒・分の繰り上がり補正込み）
    """
    v = abs(deg)
    d = int(v)
    m_float = (v - d) * 60.0
    m = int(m_float)
    s = int(round((m_float - m) * 60.0))
    if s == 60:
        s = 0
        m += 1
    if m == 60:
        m = 0
        d += 1
    return f"{d:02d}:{m:02d}:{s:02d}"


def julday_utc(y: int, m: int, d: int, hh: float) -> float:
    """
    UT（協定世界時）でのユリウス日を返す。
    - y/m/d: グレゴリオ暦
    - hh: 小数時間（例: 14.5 = 14:30）
    """
    return swe.julday(y, m, d, hh, swe.GREG_CAL)


def _calc_ut_safe(jd_ut: float, body: int, flags: int) -> Tuple[float, float, float, float, float, float]:
    """
    pyswisseph の戻り値差（(tuple), ((tuple), retflags), 3要素/6要素）を吸収して
    (lon, lat, dist, lon_spd, lat_spd, dist_spd) に正規化する。
    角度は 0..360 に正規化。
    """
    res = swe.calc_ut(jd_ut, body, flags)

    # ((...), retflags) 形式の吸収
    if isinstance(res, (tuple, list)) and len(res) == 2 and isinstance(res[0], (tuple, list)):
        vals = res[0]
    else:
        vals = res

    if len(vals) >= 6:
        lon, lat, dist, lon_spd, lat_spd, dist_spd = vals[:6]
    elif len(vals) >= 3:
        lon, lat, dist = vals[:3]
        lon_spd = lat_spd = dist_spd = 0.0
    else:
        lon = vals[0] if len(vals) > 0 else 0.0
        lat = dist = lon_spd = lat_spd = dist_spd = 0.0

    return (float(lon) % 360.0, float(lat), float(dist), float(lon_spd), float(lat_spd), float(dist_spd))


def calc_planet(jd_ut: float, p: str, node_type: NodeType) -> Tuple[float, float]:
    """
    Sidereal ecliptic longitude [0..360), speed [deg/day].
    p: 'Su','Mo','Ma','Me','Ju','Ve','Sa','Ra','Ke'
    - Lahiri sidereal（set_sid_mode済み前提）/ SWIEPH / SPEED
    """
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED

    if p == "Ra":
        p_id = swe.MEAN_NODE if node_type == "Mean" else swe.TRUE_NODE
        lon, lat, dist, lon_spd, lat_spd, dist_spd = _calc_ut_safe(jd_ut, p_id, flags)
        return lon % 360.0, float(lon_spd)

    if p == "Ke":
        p_id = swe.MEAN_NODE if node_type == "Mean" else swe.TRUE_NODE
        lon_ra, lat, dist, lon_spd_ra, lat_spd, dist_spd = _calc_ut_safe(jd_ut, p_id, flags)
        lon_ke = (lon_ra + 180.0) % 360.0
        # 速度は 0.0（運用上十分）。必要なら -lon_spd_ra を採用する設計も可能。
        return lon_ke, 0.0

    p_id = {
        "Su": swe.SUN, "Mo": swe.MOON, "Ma": swe.MARS, "Me": swe.MERCURY,
        "Ju": swe.JUPITER, "Ve": swe.VENUS, "Sa": swe.SATURN,
    }[p]

    lon, lat, dist, lon_spd, lat_spd, dist_spd = _calc_ut_safe(jd_ut, p_id, flags)
    return lon % 360.0, float(lon_spd)


def calc_asc_long(jd_ut: float, lat: float, lon: float) -> float:
    """
    サイドリアル（Lahiri）ASC黄経を 0..360 で返す。
    - Whole Sign 指定（'W'）だが、ASCそのものはハウス系に依らず同一。
    - sidereal化は flags = swe.FLG_SIDEREAL で指示。
    """
    flags = swe.FLG_SIDEREAL
    cusps, ascmc = swe.houses_ex(jd_ut, lat, lon, b'W', flags)
    asc = ascmc[0] % 360.0
    return float(asc)


def pack_sidereal_point(long_deg: float) -> Dict:
    """
    サイドリアル黄経（0..360）から
    { "sign":略号, "degree":0..29.99, "nakshatra":{"name","pada"} } を返す。
    """
    sign = sign_abbr_of(long_deg)
    deg = fmt_deg_2(deg_in_sign(long_deg))
    na_abbr, na_full, pada = nakshatra_of(long_deg)
    return {
        "sign": sign,
        "degree": deg,
        "nakshatra": {
            "name": na_full,
            "pada": pada
        }
    }


def pack_planet(long_deg: float, speed: float) -> Dict:
    """
    pack_sidereal_point に speed 数値（丸め済み）を付与した便宜関数。
    （現行設計では D1 側で speed の dict化や省略判定を行うため、
      直接の利用は推奨しないが互換のため残置）
    """
    base = pack_sidereal_point(long_deg)
    base["speed"] = fmt_speed_3(speed)
    return base
