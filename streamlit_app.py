# streamlit_app.py
import json
from datetime import date, datetime
from typing import Optional, cast, Literal
import re

import streamlit as st

# ---- calc imports ----
from calc import (
    julday_utc, calc_planet, calc_asc_long,
    prune_and_validate, pretty_json_inline_lists
)
from calc.ephemeris import get_ayanamsa_str_deg
from calc.base import (
    nakshatra_of, sign_abbr_of, deg_in_sign, fmt_deg_2,
    SIGNS, PLANETS, nakshatra_percent_left
)
from calc.d1 import build_d1
from calc.d9 import build_d9
from calc.d20 import build_d20
from calc.d60 import build_d60
from calc.jaimini import assign_chara_karaka, karakamsa_sign_for_ak, arudha_lagna, upapada_lagna
from calc.varga import d9_sign_and_degree
from calc.panchanga import tithi_info
from calc.enrich import Chart, enrich_d1, apply_varga_flags

# =======================================================
# Streamlit page configuration（最初の Streamlit コマンドに）
# =======================================================
st.set_page_config(
    page_title="JyotiSON | Jyotish Chart JSON Generator for AI",
    page_icon="☸️",
    layout="centered",
)

# =======================================================
# 1) セッション状態の初期化
# =======================================================
st.session_state.setdefault("lang", "EN")  # デフォルトは英語

# URLクエリからの初期化は「最初の 1 回だけ」にする
if "lang_initialized_from_query" not in st.session_state:
    params = st.query_params
    if "lang" in params and params["lang"] in ("EN", "JP"):
        st.session_state.lang = params["lang"]
    st.session_state.lang_initialized_from_query = True

# ---- 翻訳辞書 ----
LANG_DICT = {
    "JP": {
        "subtitle": "AI向けインド占星術チャートデータ生成ツール",
        "engine": "エンジン", "model": "計算モデル", "ref": "準拠",
        "engine_swiss": "Swiss Ephemeris", "model_drik": "Drik（観測準拠）", "ref_lahiri": "Lahiri（サイデリアル）",
        "input_bd": "出生情報の入力",
        "name": "名前", "gender": "性別", "unknown": "不明", "male": "男性", "female": "女性",
        "birth": "出生日", "birth_help": "YYYY/MM/DD 形式で入力, 時は24時間制",
        "Hr": "時 (24H)", "Min": "分", "Sec": "秒",
        "geo": "出生地（初期値は東京）", "geo_paste": "Googleマップの座標を貼り付け",
        "geo_help": "右クリックでコピーした数値をそのまま貼り付けてください",
        "geo_ph": "例: 35.6812, 139.7671",
        "geo_success": "座標を認識しました: 緯度 {default_lat} / 経度 {default_lon}",
        "geo_error": "無効な座標形式です。35.123, 139.456 のような数値を入力してください。",
        "lat": "緯度（北緯+）", "lon": "経度（東経+）", "tz": "UTCオフセット",
        "output_settings": "出力方法の設定", "expander": "クリックで展開",
        "node_type": "ノードの計算", "node_mean": "Mean Node（平均）", "node_true": "True Node（真）",
        "ck_mode": "Chara Karaka", "ck_8": "8（Rahu含む）", "ck_7": "7（Rahu除外）",
        "divisions": "分割図",
        "btn_generate": "AI向けJSONを生成（プレビュー）",
        "speed": "速度を出力に含む（retrograde 以外）",
        "lordship": "支配関係を出力に含む（lords/aspects）",
        "minimize": "出力するJSONを最小化（スペース・改行なし）",
        "d1": "D1 Rashi（基本）* 必須",
        "d9": "D9 Navamsa（本質層）",
        "d20": "D20 Vimsamsa（霊性層）",
        "d60": "D60 Shashtyamsa（カルマ層）",
        "preview": "プレビュー（JSON 内容確認）",
        "download": "最小化JSONをダウンロード（{file_name}）",
    },
    "EN": {
        "subtitle": "Jyotish Chart JSON Generator for AI",
        "engine": "Engine", "model": "Model", "ref": "Reference",
        "engine_swiss": "Swiss Ephemeris", "model_drik": "Drik (Observational)", "ref_lahiri": "Lahiri (Sidereal)",
        "input_bd": "Input Birth Details",
        "name": "Name", "gender": "Gender", "unknown": "Unknown", "male": "Male", "female": "Female",
        "birth": "Birth Date", "birth_help": "Enter date in YYYY/MM/DD format, time in 24-hour format",
        "Hr": "Hour (24H)", "Min": "Minute", "Sec": "Second",
        "geo": "Birth Place (Default: Tokyo)", "geo_paste": "Paste Google Map Coordinates",
        "geo_help": "Right-click to copy the values and paste them directly",
        "geo_ph": "e.g. 35.6812, 139.7671",
        "geo_success": "Coordinates recognized: Latitude {default_lat} / Longitude {default_lon}",
        "geo_error": "Invalid coordinate format. Please enter numbers like 35.123, 139.456.",
        "lat": "Latitude (North +)", "lon": "Longitude (East +)", "tz": "UTC Offset",
        "output_settings": "Output Settings", "expander": "Click to expand",
        "node_type": "Node Calculation", "node_mean": "Mean Node", "node_true": "True Node",
        "ck_mode": "Chara Karaka", "ck_8": "8 (Including Rahu)", "ck_7": "7 (Excluding Rahu)",
        "divisions": "Divisional Charts",
        "btn_generate": "Generate JSON for AI (Preview)",
        "speed": "Include speed status outputs",
        "lordship": "Include lordship relations (lords/aspects)",
        "minimize": "Minimize JSON output (no spaces/newlines)",
        "d1": "D1 Rashi (Basic) * Required",
        "d9": "D9 Navamsa (Essence)",
        "d20": "D20 Vimsamsa (Spiritual)",
        "d60": "D60 Shashtyamsa (Karmic)",
        "preview": "Preview (JSON content)",
        "download": "Download minified JSON ({file_name})",
    },
}

def t(key: str) -> str:
    lang = st.session_state.get("lang", "EN")
    # 念のための安全策（異常値時は EN へフォールバック：書き換えはしない）
    if lang not in ("EN", "JP"):
        lang = "EN"
    return LANG_DICT[lang][key]

# --- 値の正規化（以前のラベル値 → 内部キー）---

# gender: '不明'/'Unknown'/'男性'/'女性' → 'unknown'/'male'/'female'
if "gender" in st.session_state:
    g = st.session_state["gender"]
    if g in ("不明", "Unknown"):
        st.session_state["gender"] = "unknown"
    elif g in ("男性", "Male"):
        st.session_state["gender"] = "male"
    elif g in ("女性", "Female"):
        st.session_state["gender"] = "female"

# node_type: 'Mean Node（平均）' 等 → 'Mean' / 'True'
if "node_type" in st.session_state:
    nt = st.session_state["node_type"]
    if isinstance(nt, str):
        if "Mean" in nt or "平均" in nt:
            st.session_state["node_type"] = "Mean"
        elif "True" in nt or "真" in nt:
            st.session_state["node_type"] = "True"

# 初期値の保証（まだ何も入っていない場合のデフォルト）
st.session_state.setdefault("gender", "unknown")
st.session_state.setdefault("node_type", "True")

# ck_mode は文字列 "8"/"7" で統一（※以前合意した安定パターン）
cm = st.session_state.get("ck_mode", "8")
if isinstance(cm, str):
    st.session_state["ck_mode"] = "7" if cm.strip().startswith("7") else "8"
elif cm in (8, 7):
    st.session_state["ck_mode"] = "7" if cm == 7 else "8"
else:
    st.session_state["ck_mode"] = "8"

# =======================================================
# 2) ページ上部の余白/CSS・ヘッダー
# =======================================================
st.markdown("<style>.block-container {padding-top: 2rem;}</style>", unsafe_allow_html=True)

st.markdown(
    """
    <style>
    .header-container {text-align: center; padding: 1.5rem 0 2rem 0; font-family: 'Inter', 'sans-serif';}
    .logo-text {font-size: 4rem; font-weight: 800; letter-spacing: -2px; margin-bottom: 0; line-height: 1;}
    .yoti {opacity: 0.5; font-weight: 500; letter-spacing: -4px; padding: 0 2px;}
    .subtitle-text {font-size: 1rem; font-weight: 500; letter-spacing: 2px; text-transform: uppercase;
        opacity: 0.7; margin-top: 0.9rem;}
    /* st.caption の下の余白を削る */
    div[data-testid="stCode"] code {font-size: 0.8rem !important;}
    div[data-testid="stExpander"], div.stInfo {border: none;
        border-radius: 10px;
        background-color: rgba(128, 128, 128, 0.05);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ヘッダー & 言語トグル
col1, col2 = st.columns([6, 1])
with col1:
    st.markdown(
        f"""
        <div class="header-container">
          <div class="logo-text">J<span class="yoti">yoti</span>SON</div>
          <div class="subtitle-text">{t('subtitle')}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
with col2:
    # ロゴ高さに合わせた余白
    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

    st.radio(
        label="Language",
        options=["EN", "JP"],
        key="lang",                 # ← 状態はセッションに直結
        horizontal=False,
        # label_visibility="collapsed"  # ← ラベル非表示でスッキリ
    )

# EN が選ばれたときだけ ?lang を URL から消す
if st.session_state.lang == "EN":
    qp = st.query_params  # 直接操作する
    if "lang" in qp:
        del qp["lang"]

# =======================================================
# 3) Engine Info (Grid Layout)
# =======================================================
empty_l, c1, c2, c3, empty_r = st.columns([0.5, 2, 2, 2, 0.5])
with c1:
    st.caption(f"⚙️ **{t('engine')}**")
    st.code(f"{t('engine_swiss')}", language=None)
with c2:
    st.caption(f"🔬 **{t('model')}**")
    st.code(f"{t('model_drik')}", language=None)
with c3:
    st.caption(f"📍 **{t('ref')}**")
    st.code(f"{t('ref_lahiri')}", language=None)

# --- Googleマップ貼り付け文字列の汎用パーサ（最初の2つの浮動小数を抽出） ---

def parse_latlon_any(s: str) -> tuple[float, float] | None:
    """
    文字列から最初の2つの浮動小数点数を抽出して (lat, lon) を返す。
    - マイナス記号/小数点に対応
    - URLや度数表記、スペース区切りなどもカバー
    - 値域チェック（lat: -90..90, lon: -180..180）
    """
    if not s:
        return None
    nums = re.findall(r"[-+]?\d+(?:\.\d+)?", s)
    if len(nums) >= 2:
        lat, lon = float(nums[0]), float(nums[1])
        if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
            return lat, lon
    return None

# 入力UIの直前（with st.container(border=True): の上でもOK）
st.session_state.setdefault("lat", 35.68120)
st.session_state.setdefault("lon", 139.76710)
st.session_state.setdefault("tz", 9.0)

# =======================================================
# 4) 入力UI（全ウィジェットに固定 key、内部値固定＋format_func）
# =======================================================
st.subheader(t("input_bd"))
with st.container(border=True):
    a1, a2 = st.columns([1.4, 1])
    with a1:
        user_name = st.text_input(t("name"), value=(st.session_state.get("name") or "Guest"), key="name") or "Guest"
    with a2:
        gender = st.selectbox(
            t("gender"),
            options=["unknown", "male", "female"],      # 内部キー固定
            format_func=lambda k: t(k),                 # 表示だけ翻訳
            key="gender",                               # ← indexを使わず、keyに任せる
        )

    b1, b2, b3, b4 = st.columns([1.8, 1, 1, 1])
    with b1:
        birth_date = st.date_input(
            t("birth"),
            value=st.session_state.get("birth_date", date(1990, 1, 1)),
            min_value=date(1, 1, 1),
            max_value=date(2999, 12, 31),
            key="birth_date",
        )
    with b2:
        h = st.number_input(t("Hr"), min_value=0, max_value=23, value=st.session_state.get("hour", 12), step=1, key="hour")
    with b3:
        m = st.number_input(t("Min"), min_value=0, max_value=59, value=st.session_state.get("min", 0), step=1, key="min")
    with b4:
        s = st.number_input(t("Sec"), min_value=0, max_value=59, value=st.session_state.get("sec", 0), step=1, key="sec")

    st.write(t("geo"))
    geo_paste = st.text_input(
        t("geo_paste"),
        placeholder=t("geo_ph"),
        help=t("geo_help"),
        key="geo_paste",
    )

    default_lat, default_lon = 35.68120, 139.76710
    if geo_paste:
        res = parse_latlon_any(geo_paste)
        if res:
            default_lat, default_lon = res
            # セッションにだけセット（このランでは value を使わない）
            st.session_state["lat"] = default_lat
            st.session_state["lon"] = default_lon
            st.success(t("geo_success").format(default_lat=default_lat, default_lon=default_lon))
        else:
            st.error(t("geo_error"))

    g1, g2, g3 = st.columns([1, 1, 1])
    with g1:
        # ❌ 旧: value=st.session_state.get("lat", default_lat)
        # ✅ 新: value を渡さない（Session State に任せる）
        geo_lat = st.number_input(
            t("lat"),
            min_value=-90.0,
            max_value=90.0,
            format="%.5f",
            key="lat",
        )

    with g2:
        geo_lon = st.number_input(
            t("lon"),
            min_value=-180.0,
            max_value=180.0,
            format="%.5f",
            key="lon",
        )

    with g3:
        tz_offset = st.number_input(
            t("tz"),
            step=0.5,
            format="%.1f",
            key="tz",
        )

    # 性別コード（内部値から変換）
    GENDER_MAP = {"unknown": "Unknown", "male": "Male", "female": "Female"}
    gender_code = GENDER_MAP.get(gender, "Unknown")

# =======================================================
# 5) 出力設定UI（内部値固定＋format_func／固定 key）
# =======================================================
st.subheader(t("output_settings"))
with st.expander(t("expander"), expanded=True):
    c1, c2 = st.columns([1, 1])
    with c1:
        # --- Node Type ---
        node_type_label = st.radio(
            t("node_type"),
            options=["Mean", "True"],
            format_func=lambda k: t("node_mean") if k == "Mean" else t("node_true"),
            key="node_type",     # ✅ index を指定しない
        )
        node_type: Literal["Mean", "True"] = cast(Literal["Mean", "True"], node_type_label)

        # --- Chara Karaka（内部は文字列 "8"/"7"）---
        ck_mode_str = st.radio(
            t("ck_mode"),
            options=["8", "7"],  # ← 文字列で固定
            format_func=lambda s: t("ck_8") if s == "8" else t("ck_7"),
            key="ck_mode",        # ✅ index を指定しない
        )
        # 計算で使うのは int に変換
        ck_mode = 8 if ck_mode_str == "8" else 7

        include_speed = st.checkbox(t("speed"), value=st.session_state.get("include_speed", False), key="include_speed")
        # include_lordship = st.checkbox(t("lordship"), value=st.session_state.get("include_lordship", True), key="include_lordship")
        minimize = st.checkbox(t("minimize"), value=st.session_state.get("minimize", True), key="minimize")

    with c2:
        st.write(t("divisions"))
        include_d1 = st.checkbox(t("d1"), value=st.session_state.get("include_d1", True), key="include_d1")
        include_d9 = st.checkbox(t("d9"), value=st.session_state.get("include_d9", True), key="include_d9")
        include_d20 = st.checkbox(t("d20"), value=st.session_state.get("include_d20", False), key="include_d20")
        include_d60 = st.checkbox(t("d60"), value=st.session_state.get("include_d60", False), key="include_d60")

go = st.button(t("btn_generate"), type="primary", key="btn_generate")

# =======================================================
# Utils
# =======================================================

def _sanitize_filename(text: str) -> str:
    t_ = text.strip()
    t_ = re.sub(r"[^\w\-]+", "_", t_, flags=re.UNICODE)
    return t_ or "Guest"

def _yyyymmdd(d: date) -> str:
    return f"{d.year:04d}{d.month:02d}{d.day:02d}"

def format_tz_offset_for_iso(tz: float) -> str:
    sign = "+" if tz >= 0 else "-"
    v = abs(tz)
    hours = int(v)
    minutes = int(round((v - hours) * 60))
    return f"{sign}{hours:02d}:{minutes:02d}"

def reorder_planet_entry_order(d: dict) -> dict:
    """
    惑星エントリのキー順を 'sign, degree, house, nakshatra, retrograde, dignity, speed' に統一。
    """
    if not isinstance(d, dict):
        return d
    ordered = {}
    for k in ("sign", "degree", "house", "nakshatra", "retrograde", "dignity", "speed"):
        if k in d:
            ordered[k] = d[k]
    for k, v in d.items():
        if k not in ordered:
            ordered[k] = v
    return ordered

def apply_ordering_to_chart(chart_dict: Optional[dict]) -> None:
    """
    charts.* の D1/D9 出力に対し、Ascとplanetのキー順序を整える。
    """
    if not isinstance(chart_dict, dict):
        return
    if "Asc" in chart_dict and isinstance(chart_dict["Asc"], dict):
        asc = chart_dict["Asc"]
        asc_ordered = {}
        for k in ("sign", "degree"):
            if k in asc:
                asc_ordered[k] = asc[k]
        for k, v in asc.items():
            if k not in asc_ordered:
                asc_ordered[k] = v
        chart_dict["Asc"] = asc_ordered
    if "planets" in chart_dict and isinstance(chart_dict["planets"], dict):
        for pkey, entry in list(chart_dict["planets"].items()):
            chart_dict["planets"][pkey] = reorder_planet_entry_order(entry)

# =======================================================
# 6) 生成（計算ロジックはそのまま）
# =======================================================
if go:
    # 0) 入力 → UTC → JD(UT)
    hh = float(h) + float(m) / 60.0 + float(s) / 3600.0
    hh_utc = hh - float(tz_offset)
    jd_ut = julday_utc(birth_date.year, birth_date.month, birth_date.day, hh_utc)

    # 1) Ayanamsa（表示＋数値）
    aya_str, aya_deg_float = get_ayanamsa_str_deg(jd_ut)

    # 2) 惑星計算（0..360 の sidereal 生黄経＆D1用の基本データ）
    planets_raw = {}
    for p in PLANETS:
        p_lon, spd = calc_planet(jd_ut, p, node_type)
        na_abbr, na_full, pada = nakshatra_of(p_lon)
        planets_raw[p] = {
            "_lon360": float(p_lon),
            "sign": sign_abbr_of(p_lon),
            "degree": fmt_deg_2(deg_in_sign(p_lon)),
            "nakshatra": {"name": na_full, "pada": pada},
            "speed": round(spd, 3),
        }

    # 3) ASC（サイドリアル）
    asc_long = calc_asc_long(jd_ut, geo_lat, geo_lon)

    # 4) charts 初期化
    vargas: dict[str, Chart] = {}

    # 5) D1（ON時のみ）
    if include_d1:
        d1 = build_d1(
            asc_long,
            planets_raw,
            include_speed_flags=include_speed,
        )

        # Moon に Tithi/Nakshatra の %残 を付与
        if "Mo" in planets_raw and "planets" in d1:
            ti_name, paksha, ti_left = tithi_info(
                mo_long=planets_raw["Mo"]["_lon360"],
                su_long=planets_raw["Su"]["_lon360"],
            )
            mo_entry = d1["planets"].get("Mo", {})
            mo_entry["tithi"] = {"name": ti_name, "paksha": paksha, "percent_left": ti_left}
            na_left = nakshatra_percent_left(planets_raw["Mo"]["_lon360"])
            if isinstance(mo_entry.get("nakshatra"), dict):
                mo_entry["nakshatra"]["percent_left"] = na_left
            d1["planets"]["Mo"] = mo_entry

        # Jaimini（CK + Karakamsa + AL/UL）
        deg_by, abs_by = {}, {}
        for p_key, rec in planets_raw.items():
            if p_key == "Ke":
                continue
            lon = rec.get("_lon360")
            if lon is None:
                continue
            abs_by[p_key] = float(lon)
            deg_by[p_key] = float(lon % 30.0)

        ck_map = assign_chara_karaka(deg_by, mode=ck_mode, abs_long_by_planet=abs_by)
        ak = ck_map.get("AK")
        kk_sign = karakamsa_sign_for_ak(abs_by, ak) if ak else None

        jai = dict(ck_map)
        if kk_sign:
            jai["karakamsa_sign"] = kk_sign
        jai["arudha_lagna"] = arudha_lagna(d1)
        jai["upapada_lagna"] = upapada_lagna(d1)

        d1["jaimini"] = jai
        vargas["D1"] = cast(Chart, d1)

        planets_long = {p: rec["_lon360"] for p, rec in planets_raw.items()}

        if include_d9:
            vargas["D9"] = cast(Chart, build_d9(asc_long, planets_long))

        vargas["D1"] = cast(
            Chart,
            enrich_d1(
                cast(Chart, vargas["D1"]),
                planets_raw,
                d9=cast(Optional[Chart], vargas.get("D9")),
            )
        )

        if include_d20:
            vargas["D20"] = cast(Chart, build_d20(asc_long, planets_long, include_exaltation=True))
        if include_d60:
            vargas["D60"] = cast(Chart, build_d60(asc_long, planets_long, include_exaltation=False))

        if include_d1 and "D1" in vargas:
            d1_chart: Chart = cast(Chart, vargas["D1"])
            if include_d9 and "D9" in vargas:
                vargas["D9"] = apply_varga_flags(cast(Chart, vargas["D9"]), d1_chart, "D9")
            if include_d20 and "D20" in vargas:
                vargas["D20"] = apply_varga_flags(cast(Chart, vargas["D20"]), d1_chart, "D20")
            if include_d60 and "D60" in vargas:
                vargas["D60"] = apply_varga_flags(cast(Chart, vargas["D60"]), d1_chart, "D60")

    # 7) キー順の整形（存在時のみ）
    apply_ordering_to_chart(cast(dict, vargas.get("D1")))
    apply_ordering_to_chart(cast(dict, vargas.get("D9")))

    # --- ダシャ（Vimshottari） ---
    from calc.dasha import compute_vimshottari_md_with_context, _tz_from_offset_hours

    tz = _tz_from_offset_hours(tz_offset)
    birth_dt_local = datetime(birth_date.year, birth_date.month, birth_date.day, int(h), int(m), int(s), tzinfo=tz)
    moon_lon = planets_raw["Mo"]["_lon360"]

    extra_dasha = compute_vimshottari_md_with_context(
        birth_dt_local=birth_dt_local,
        tz_offset=tz_offset,
        moon_abs_long=moon_lon,
        horizon_years=110
    )

    # 8) birth ISO8601
    birth_iso = (
        f"{birth_date.isoformat()}T"
        f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
        f"{format_tz_offset_for_iso(tz_offset)}"
    )

    # 出力生成時刻（tz付き ISO8601、秒まで）
    tz = _tz_from_offset_hours(tz_offset)
    output_at = datetime.now(tz).isoformat(timespec="seconds")

    # 9) トップレベル JSON
    out = {
        "schema": "kundali_llm_v1",
        "generator": {
            "tool": "JyotiSON",
            "version": "1.0-beta",
            "url": "https://jyotison.streamlit.app/",
            "output_at": output_at,
            "purpose": "LLM_vedic_astrology_analysis"
        },
        "birth_data": {
            "name": user_name,
            "gender": gender_code,
            "birth": birth_iso,
            "latitude": float(f"{geo_lat:.2f}"),
            "longitude": float(f"{geo_lon:.2f}"),
        },
        "calculation_settings": {
            "zodiac": "Sidereal",
            "ayanamsa": {"name": "Lahiri", "degree": round(aya_deg_float, 6)},
            "node_type": node_type,
            "house_system": "Whole Sign",
            "ephemeris": "Swiss Ephemeris",
        },
        "charts": vargas,
        "dasha": extra_dasha
    }

    # 10) バリデーション → 表示/保存
    out = prune_and_validate(out)
    txt_pretty = pretty_json_inline_lists(out, indent=2)
    txt_min = json.dumps(out, ensure_ascii=False, separators=(",", ":")) if minimize else txt_pretty

    st.subheader(t("preview"))
    st.code(txt_pretty, language="json")

    fname_base = _sanitize_filename(user_name) + "_" + _yyyymmdd(birth_date)
    file_name = f"{fname_base}.json"
    st.download_button(
        label=t("download").format(file_name=file_name),
        data=txt_min.encode("utf-8"),
        file_name=file_name,
        mime="application/json",
        use_container_width=True,
    )

# --- フッター ---
st.write("---")
st.markdown(
    """
<div style="text-align:center;">
  <span style="color:#888; font-size:0.85rem; font-style:italic; line-height:1.6;">
    May those who hold this tool hear the harmony of the planetary alignments,<br/>
    and find their soul returning to the profound peace that dwells within ancient wisdom.
  </span>
</div>
""",
    unsafe_allow_html=True,
)
