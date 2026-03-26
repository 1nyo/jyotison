# streamlit_app.py
import json
from datetime import date, datetime
from typing import Optional, cast, Literal
import re

import streamlit as st

# ---- ui imports ----
from ui.i18n import t, validate_lang_dict
from ui.geo_timezone import (
    ensure_geo_tz_state,
    mark_tz_dirty,
    clear_geo_paste,
    on_latlon_manual_change,
    on_tz_manual_change,
    handle_geo_paste,
    render_geo_message,
)
from ui.presets import (
    ensure_preset_state,
    on_preset_slider_change,
    on_manual_option_changed,
    current_profile_for_desc,
)

# ---- input imports ----
from input.location import parse_location_input

# ---- calc imports ----
from calc import (
    julday_utc, calc_planet, calc_asc_long,
    prune_and_validate, pretty_json_inline_lists
)
from calc.timezone import resolve_timezone
from calc.ephemeris import get_ayanamsa_str_deg, NodeType
from calc.base import (
    nakshatra_of, sign_abbr_of, deg_in_sign, fmt_deg_2,
    SIGNS, PLANETS, nakshatra_percent_left
)
from calc.d1 import build_d1
from calc.d9 import build_d9
from calc.varga import build_varga
from calc.jaimini import assign_chara_karaka, karakamsa_sign_for_ak, arudha_lagna, upapada_lagna
from calc.panchanga import tithi_info
from calc.enrich import Chart, enrich_d1, apply_varga_flags

# ---- output imports ----
from output.filters import apply_output_options

# =======================================================
# Streamlit page configuration（最初の Streamlit コマンドに）
# =======================================================
st.set_page_config(
    page_title="JyotiSON | Jyotish Chart JSON Generator for AI",
    page_icon="☸️",
    layout="centered",
)
validate_lang_dict(strict=False)

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

# 初期値の保証（まだ何も入っていない場合のデフォルト）
st.session_state.setdefault("gender", None)
st.session_state.setdefault("node_type", "True")

# ck_mode は内部表現は常に "8" or "7"
st.session_state.setdefault("ck_mode", "8")

# 何が来ても最終的には "8"/"7" に丸める
ck = st.session_state["ck_mode"]
if ck in (8, 7):
    ck = "7" if ck == 7 else "8"
elif ck not in ("8", "7"):
    ck = "8"
st.session_state["ck_mode"] = ck

# --- cache wrapper ---
@st.cache_data(show_spinner=False)
def parse_location_input_cached(text: str):
    return parse_location_input(text)


# =======================================================
# 2) ページ上部の余白/CSS・ヘッダー（EN/JP 切り替えもここ）
# =======================================================
st.markdown("<style>.block-container {padding-top: 2rem;}</style>", unsafe_allow_html=True)

st.markdown(
    """
    <style>
    .header-container {text-align: center; padding: 0 0 1.5rem 0; font-family: 'Inter', 'sans-serif';}
    .logo-text {font-size: 4rem; font-weight: 800; letter-spacing: -2px; margin-bottom: 0; line-height: 1;}
    .yoti {opacity: 0.8; font-weight: 500; letter-spacing: -4px; padding: 0 2px;}
    .version-text { font-size: 1rem; vertical-align: super; opacity: 0.5; margin-left: 2px; position: relative; top: -0.8rem; font-weight: 400; letter-spacing: 0; }
    .subtitle-text {font-size: 1rem; font-weight: 500; letter-spacing: 2px; text-transform: uppercase;
        opacity: 0.85; margin-top: 0.9rem;}
    /* st.caption の下の余白を削る */
    div[data-testid="stCode"] code {font-size: 0.8rem;}
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
          <div class="logo-text">J<span class="yoti">yoti</span>SON
          <span class="version-text">v1.1</span></div>
          <div class="subtitle-text">{t('subtitle')}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
with col2:
    st.radio(
        label="Language",
        options=["EN", "JP"],
        key="lang",                 # ← 状態はセッションに直結
        horizontal=False,
        # label_visibility="collapsed"  # ← ラベル非表示でスッキリ
    )

# URL の ?lang と、現在の選択 lang が違う場合だけ ?lang を URL から消す
qp = st.query_params  # dict-like
if "lang" in qp and qp["lang"] != st.session_state.lang:
    del qp["lang"]

# =======================================================
# 3) Engine Info (Grid Layout)
# =======================================================
empty_l, c1, c2, c3, empty_r = st.columns([0.5, 2, 2, 2, 0.5])

with c1:
    st.caption(f":material/settings: **{t('engine')}**")
    st.code(t("engine_swiss"), language=None)

with c2:
    st.caption(f":material/science: **{t('model')}**")
    st.code(t("model_drik"), language=None)

with c3:
    st.caption(f":material/public: **{t('ref')}**")
    st.code(t("ref_lahiri"), language=None)


# 入力UIの直前（with st.container(border=True): の上でもOK）
st.session_state.setdefault("lat", 35.68120)
st.session_state.setdefault("lon", 139.76710)
st.session_state.setdefault("tz", 9.0)

# =======================================================
# 4) 入力UI（全ウィジェットに固定 key、内部値固定＋format_func）
# =======================================================
st.subheader(
    f":material/assignment_ind: {t('input_bd')}"
    )
with st.container(border=True):
    a1, a2, = st.columns([1.5, 1])
    with a1:
        user_name = st.text_input(t("name"), value=(st.session_state.get("name") or "Guest"), key="name") or "Guest"

    with a2:
        lang = st.session_state.get("lang", "EN")
        gender_widget_key = f"gender_ui_{lang}"

        # 言語切替を検知（popしない）
        prev_lang = st.session_state.get("_prev_lang_for_gender")
        if prev_lang != lang:
            # 内部値がある場合だけ、新言語側のkeyへ事前注入（ウィジェット生成前なのでOK）
            if st.session_state.get("gender") in ("male", "female"):
                st.session_state[gender_widget_key] = st.session_state["gender"]
            else:
                # 未選択なら新言語側も未選択に（既存値が残っていたら消す）
                st.session_state.pop(gender_widget_key, None)

            st.session_state["_prev_lang_for_gender"] = lang

        # index=None 固定：クリア（○×）が効く状態を維持 [1](https://docs.streamlit.io/develop/concepts/architecture/widget-behavior)[2](https://stackoverflow.com/questions/78625588/streamlitapiexception-st-session-state-user-question-cannot-be-modified-after-t)
        gender_ui = st.selectbox(
            t("gender"),
            options=["male", "female"],
            index=None,
            key=gender_widget_key,
            format_func=lambda k: t(k),
            placeholder=t("choose"),
        )

        st.session_state["gender"] = gender_ui

    b1, b2, b3, b4 = st.columns([1.8, 1, 1, 1])
    with b1:
        birth_date = st.date_input(
            t("birth"),
            value=st.session_state.get("birth_date", date(1990, 1, 1)),
            min_value=date(1, 1, 1),
            max_value=date(2999, 12, 31),
            key="birth_date",
            on_change=mark_tz_dirty,  # 日付が変わったら tz_dirty を True にする
        )
    with b2:
        h = st.number_input(t("Hr"), min_value=0, max_value=23, value=st.session_state.get("hour", 12), step=1, key="hour", on_change=mark_tz_dirty)
    with b3:
        m = st.number_input(t("Min"), min_value=0, max_value=59, value=st.session_state.get("min", 0), step=1, key="min", on_change=mark_tz_dirty)
    with b4:
        s = st.number_input(t("Sec"), min_value=0, max_value=59, value=st.session_state.get("sec", 0), step=1, key="sec", on_change=mark_tz_dirty)

    st.markdown(
    f"""
    {t("geo")} <span style="font-size:0.85rem;">{t('geo_gmap')}
    <a href="https://www.google.com/maps" target="_blank">
    :material/open_in_new: {t("gmap")}</a>
    </span>
    """,
    unsafe_allow_html=True,
    )

    # ① 入力行
    g1, g2, g3, g4 = st.columns([5, 0.9, 2.9, 3])

    with g1:
        geo_paste = st.text_input(
            t("geo_paste"),
            placeholder=t("geo_ph"),
            help=t("geo_help"),
            key="geo_paste",
        )

    with g2:
        # 貼り付け欄の右にクリアボタンを配置
        st.markdown("<div style='height: 1.8rem'></div>", unsafe_allow_html=True)
        st.button("✕", help=t("geo_clear"), on_click=clear_geo_paste)

    # ② メッセージ表示用（横幅フル：columns の外に置く）
    geo_msg = st.empty()

    # geo/tz state init（安全）
    ensure_geo_tz_state()

    # ③ 貼り付け処理（変更時のみパース＆lat/lon反映＋tz autoへ）
    handle_geo_paste(geo_paste, parse_location_input_cached)

    # ③-2 メッセージ表示（rerun-safe）
    render_geo_message(geo_msg, t, geo_paste)

    # tz 自動計算のための dirty フラグ（なければ True で初期化）
    st.session_state.setdefault("tz_dirty", True)
    st.session_state.setdefault("tz_name", "Unknown")

    # ④ lat/lon のウィジェットは「貼り付け処理の後」に作る（ここが重要）
    with g3:
        geo_lat = st.number_input(
            t("lat"),
            min_value=-90.0,
            max_value=90.0,
            format="%.5f",
            key="lat",
            on_change=on_latlon_manual_change,
        )

    with g4:
        geo_lon = st.number_input(
            t("lon"),
            min_value=-180.0,
            max_value=180.0,
            format="%.5f",
            key="lon",
            on_change=on_latlon_manual_change,
        )


    # tz 自動計算（tzウィジェット生成前）
    birth_dt = datetime(
        year=birth_date.year,
        month=birth_date.month,
        day=birth_date.day,
        hour=h, minute=m, second=s
    )

    st.session_state.setdefault("tz_mode", "auto")
    st.session_state.setdefault("tz_dirty", True)

    if st.session_state.get("tz_dirty", True):
        tz_res = resolve_timezone(
            lat=float(st.session_state["lat"]),
            lon=float(st.session_state["lon"]),
            local_dt=birth_dt,
            manual_utc_offset=(
                st.session_state["tz"]
                if st.session_state["tz_mode"] == "manual"
                else None
            ),
        )

        # calc/timezone.py の結果をそのまま反映
        st.session_state["tz_name"] = tz_res.tz_name
        st.session_state["tz"] = tz_res.utc_offset_hours
        st.session_state["tz_dst_auto"] = tz_res.is_dst
        st.session_state["tz_source"] = tz_res.source
        st.session_state["tz_confidence"] = tz_res.confidence

        st.session_state["tz_dirty"] = False

    # ---- UTC offset / TZ 表示（1行） ----
    tz_l, tz_i, tz_r = st.columns([1, 1.1, 3])

    with tz_l:
            st.markdown(
                f":material/public: "
                f"<span title='{t('tz_help')}' style='font-size:0.9rem; cursor: help;'>"
                f"{t('tz')}"
                f"</span>"
                f"<div style='margin-top: -24px;'>"  # ← ここで上の行との間隔を詰める
                f"<span style='font-size:0.85rem; color:gray; margin-left: 1rem;'>"
                f"{t('tz_auto')}"
                f"</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

    with tz_i:
        # UTCオフセットの入力（自動計算された値が初期値として入る）
        tz_offset = st.number_input(
            label="Timezone Offset",
            min_value=-12.0,
            max_value=14.0,
            step=0.25,
            format="%.2f",
            key="tz",
            label_visibility="collapsed",
            on_change=on_tz_manual_change,   # ← UTCオフセットを触ったら Manual に切り替える
        )

    with tz_r:
        # タイムゾーン名の表示（DST/標準時の状態も併記）
        tz_name = st.session_state.get("tz_name", "Unknown")
        tz_mode = st.session_state.get("tz_mode", "auto")

        # DST/Standard は「自動判定結果」だけを見る
        tz_dst_auto = st.session_state.get("tz_dst_auto")

        if tz_dst_auto is True:
            tz_suffix = "DST"
        elif tz_dst_auto is False:
            tz_suffix = "Standard"
        else:
            tz_suffix = "Unknown"

        mode_badge = "Auto" if tz_mode == "auto" else "Manual"
        icon = ":material/check:" if tz_mode == "auto" else ":material/edit:"

        st.markdown(
            f"<span style='font-size:0.85rem; color:gray; top: 0.4rem; position: relative;'>"
            f"{icon} Timezone: <b>{tz_name}</b> ({tz_suffix}) [{mode_badge}]"
            f"</span>",
            unsafe_allow_html=True,
        )


    # 性別コード（内部値から変換）
    GENDER_MAP = {"male": "Male", "female": "Female"}
    gender_code = GENDER_MAP.get(st.session_state["gender"])  # NoneならNone


ensure_preset_state(default_profile="Standard")
# =======================================================
# 5) 出力設定UI（Preset Slider + Tabs）
# =======================================================
st.subheader(
    f":material/file_json: {t('output_settings')}"
    )
with st.container(border=True):

# --- Output Level スライダー + Custom 表示 ---
    st.write(f"{t('output_level')}")
    col_slider, col_status = st.columns([7, 3])

    with col_slider:
        # スライダー本体（uitest.py と同じ構成）
        selected_level = st.select_slider(
            "preset_slider",
            options=["Basic", "Standard", "Advanced"],
            key="output_level",          # セッションに直結
            label_visibility="collapsed",
            on_change=on_preset_slider_change,
        )

        # Custom 中だけ、スライダーを薄く表示
        if st.session_state.get("is_custom", False):
            st.markdown(
                """
                <style>
                div[data-testid="stSlider"] > div {
                    opacity: 0.4;
                    transition: opacity 0.2s ease-in-out;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <style>
                div[data-testid="stSlider"] > div {
                    opacity: 1.0;
                    transition: opacity 0.2s ease-in-out;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )

    with col_status:
        # 「完璧に揃った」Custom 表示をそのまま利用
        if st.session_state.get("is_custom", False):
            st.markdown(
                """
                <div style="text-align: center; color:#FF4B4B; line-height: 12px; margin-top: -3px;">
                    <span style="font-size: 14px;">Custom</span>
                </div>
                <div style="text-align: center; color:#FF4B4B; line-height: 22px;">
                    <span style="font-size: 24px;">●</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div style="text-align: center; color:gray; opacity: 0.8; line-height: 12px; margin-top: -3px;">
                    <span style="font-size: 14px;">Custom</span>
                </div>
                <div style="text-align: center; color:gray; opacity: 0.3; line-height: 22px;">
                    <span style="font-size: 24px;">○</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ---- 説明文（current_profile に応じて表示） ----
    current_profile = current_profile_for_desc()
    st.info(t(f"preset_desc_{current_profile.lower()}"))

    # ---- Tabs Reorganized ----
    tab_basic, tab_d1, tab_varga, tab_dasha = st.tabs(
        [t("tab_basic"), t("tab_d1"), t("tab_varga"), t("tab_dasha")]
    )


# =======================================================
# BASIC 設定タブ
# =======================================================
with tab_basic:
    col_node, col_ck = st.columns([1, 1])

    with col_node:
        # --- Node Type (Mean / True) ---

        # 内部値の正規化（安全策）
        if st.session_state["node_type"] not in ("Mean", "True"):
            st.session_state["node_type"] = "True"

        lang = st.session_state.get("lang", "EN")
        node_type_widget_key = f"node_type_{lang}"

        # 内部値から index を決定
        internal = st.session_state["node_type"]
        idx = 0 if internal == "Mean" else 1

        node_type: NodeType = cast(
            NodeType,
            st.radio(
                t("node_type"),
                options=["Mean", "True"],
                index=idx,
                key=node_type_widget_key,
                format_func=lambda k: (
                    t("node_mean") if k == "Mean" else t("node_true")
                ),
            ),
        )

        # 内部値へ同期（真実はここ）
        st.session_state["node_type"] = node_type

    with col_ck:
        # --- Chara Karaka（内部は文字列 "8"/"7"）---
        ck_mode_str = st.radio(
            t("ck_mode"),
            options=["8", "7"],
            format_func=lambda s: t("ck_8") if s == "8" else t("ck_7"),
            key="ck_mode",   # session_state["ck_mode"] をそのまま使う
        )

        # 計算では int に変換
        ck_mode = 8 if ck_mode_str == "8" else 7

    # --- 2行目：minimize（columns の外） ---
    minimize = st.checkbox(
        t("minimize"),
        value=st.session_state.get("minimize", True),
        key="minimize",
    )

# =======================================================
# D1 詳細タブ（4カテゴリ構成）
# =======================================================
with tab_d1:
    d1, d2 = st.columns([1, 1])

    with d1:
        # ---- Interactions ----
        st.caption(f":material/sync_alt: {t('d1_interactions')}")
        opt_nak_lord     = st.checkbox(t("chk_nak_lord"), key="opt_nak_lord", on_change=on_manual_option_changed)
        opt_aspects      = st.checkbox(t("chk_aspects"), key="opt_aspects", on_change=on_manual_option_changed)
        opt_conjunctions = st.checkbox(t("chk_conjunctions"), key="opt_conjunctions", on_change=on_manual_option_changed)

        # ---- Planet Motion ----
        st.caption(f":material/speed: {t('d1_motion')}")
        opt_speed_status = st.checkbox(t("chk_speed_status"), key="opt_speed_status", on_change=on_manual_option_changed)

    with d2:
        # ---- Planet Conditions ----
        st.caption(f":material/assessment: {t('d1_conditions')}")
        opt_combust      = st.checkbox(t("chk_combust"), key="opt_combust", on_change=on_manual_option_changed)
        opt_planet_war   = st.checkbox(t("chk_planet_war"), key="opt_planet_war", on_change=on_manual_option_changed)
        opt_dignity_det  = st.checkbox(t("chk_dignity_detail"), key="opt_dignity_det", on_change=on_manual_option_changed)
        opt_dig_bala     = st.checkbox(t("chk_dig_bala"), key="opt_dig_bala", on_change=on_manual_option_changed)

        # ---- Special Positions ----
        st.caption(f":material/flare: {t('d1_special')}")
        opt_vargottama   = st.checkbox(t("chk_vargottama"), key="opt_vargottama", on_change=on_manual_option_changed)
        opt_gandanta     = st.checkbox(t("chk_gandanta"), key="opt_gandanta", on_change=on_manual_option_changed)

        # future (disabled)
        # st.checkbox("Mrityu Bhaga (future)", disabled=True)
        # st.checkbox("Ashtakavarga (future)", disabled=True)
        # st.checkbox("Shadbala (future)", disabled=True)

# =======================================================
# 分割図タブ 2列構成 + Varga Options
# =======================================================
with tab_varga:
    e1, e2 = st.columns(2)

    with e1:
        include_d1  = st.checkbox(t("d1"),  key="include_d1",  on_change=on_manual_option_changed)
        include_d9  = st.checkbox(t("d9"),  key="include_d9",  on_change=on_manual_option_changed)
        include_d3  = st.checkbox(t("d3"),  key="include_d3",  on_change=on_manual_option_changed)
        include_d4  = st.checkbox(t("d4"),  key="include_d4",  on_change=on_manual_option_changed)
        include_d7  = st.checkbox(t("d7"),  key="include_d7",  on_change=on_manual_option_changed)
        include_d10 = st.checkbox(t("d10"), key="include_d10", on_change=on_manual_option_changed)

    with e2:
        include_d12 = st.checkbox(t("d12"), key="include_d12", on_change=on_manual_option_changed)
        include_d16 = st.checkbox(t("d16"), key="include_d16", on_change=on_manual_option_changed)
        include_d20 = st.checkbox(t("d20"), key="include_d20", on_change=on_manual_option_changed)
        include_d24 = st.checkbox(t("d24"), key="include_d24", on_change=on_manual_option_changed)
        include_d30 = st.checkbox(t("d30"), key="include_d30", on_change=on_manual_option_changed)
        include_d60 = st.checkbox(t("d60"), key="include_d60", on_change=on_manual_option_changed)

    # ---- Varga Output Options ----
    with st.expander(t("varga_op"), expanded=False):
        varga_d9_degree = st.checkbox(t("varga_d9_deg"), key="varga_d9_degree", on_change=on_manual_option_changed)
        varga_dignity   = st.checkbox(t("varga_d3d60_dig"), key="varga_dignity", on_change=on_manual_option_changed)

# =======================================================
# ダシャータブ
# =======================================================
with tab_dasha:
    opt_vimshottari = st.checkbox(t("vimshottari"), value=True)
    st.checkbox(t("chara_dasha"), disabled=True)

# =======================================================
# 実行ボタン
# =======================================================
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
    tz_offset = float(st.session_state["tz"])
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

        planets_long = {p: rec["_lon360"] for p, rec in planets_raw.items()} # D9 以降の生成に必要なのでここで作成

    # --- D9 ---
        if include_d9:
            vargas["D9"] = cast(Chart, build_d9(asc_long, planets_long))

    # enrich_d1（D1の拡充：D9もあれば渡す）
        vargas["D1"] = cast(
            Chart,
            enrich_d1(
                cast(Chart, vargas["D1"]),
                planets_raw,
                d9=cast(Optional[Chart], vargas.get("D9")),
            )
        )

        # ------------------------------
        # D3〜D60 include フラグ一覧
        # ------------------------------
        varga_includes: dict[str, bool] = {
            "D3":  include_d3,
            "D4":  include_d4,
            "D7":  include_d7,
            "D10": include_d10,
            "D12": include_d12,
            "D16": include_d16,
            "D20": include_d20,
            "D24": include_d24,
            "D30": include_d30,
            "D60": include_d60,
        }

        # ------------------------------
        # Varga 生成（ループ統一）
        # ------------------------------
        for name, flag in varga_includes.items():
            if not flag:
                continue
            vargas[name] = cast(Chart, build_varga(name, asc_long, planets_long))

        # ------------------------------
        # retrograde / dignity コピー
        # ------------------------------
        if "D1" in vargas:
            d1_chart: Chart = cast(Chart, vargas["D1"])

            # D9 は個別（品位規則が特殊）
            if include_d9 and "D9" in vargas:
                vargas["D9"] = apply_varga_flags(
                    cast(Chart, vargas["D9"]), d1_chart, "D9"
                )

            # D3〜D60 はループで処理
            for name, flag in varga_includes.items():
                if not flag or name not in vargas:
                    continue

                # ★ Literal 型へキャストして型エラーを解消する
                kind_literal = cast(
                    Literal[
                        "D3","D4","D7","D10","D12","D16","D20","D24","D30","D60"
                    ],
                    name
                )

                vargas[name] = apply_varga_flags(
                    cast(Chart, vargas[name]), d1_chart, kind_literal
                )

    # 7) キー順の整形（存在時のみ）
    for k in ("D1","D9","D3","D4","D7","D10","D12","D16","D20","D24","D30","D60"):
        apply_ordering_to_chart(cast(dict, vargas.get(k)))
    
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

    # UTC offset をここで一度だけ確定させる（重要）
    tz_offset = st.session_state.get("tz")

    # 8) birth ISO8601
    birth_iso = (
        f"{birth_date.isoformat()}T"
        f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
        f"{format_tz_offset_for_iso(float(tz_offset) if tz_offset is not None else 0.0)}"
    )

    # 出力生成時刻（tz付き ISO8601、秒まで）
    tzinfo = _tz_from_offset_hours(float(tz_offset) if tz_offset is not None else 0.0)
    output_at = datetime.now(tzinfo).isoformat(timespec="seconds")

    # 9) トップレベル JSON
    out = {
        "schema": "kundali_llm_v1",
        "generator": {
            "tool": "JyotiSON",
            "version": "1.1",
            "url": "https://jyotison.streamlit.app/",
            "output_at": output_at,
            "purpose": "LLM_vedic_astrology_analysis"
        },
        "birth_data": {
            "name": user_name,
            "gender": gender_code,
            "birth": birth_iso,
            "latitude": float(f"{geo_lat:.4f}"),
            "longitude": float(f"{geo_lon:.4f}"),
        },

        # timezone 情報
        "timezone": {
            "name": st.session_state.get("tz_name"),
            # "utc_offset": float(st.session_state.get("tz")),
            "utc_offset": float(tz_offset) if tz_offset is not None else None,
            "dst": st.session_state.get("tz_dst_auto"),
            "source": st.session_state.get("tz_source", "auto"),
            "confidence": st.session_state.get("tz_confidence", "high"),
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

    # =======================================================
    # 出力マスク用オプション辞書（apply_output_options へ渡す）
    # =======================================================

    output_options = {
        # ---- D1 ----
        "nakshatra_lord": opt_nak_lord,
        "aspects": opt_aspects,
        "conjunctions": opt_conjunctions,
        "combust": opt_combust,
        "planet_war": opt_planet_war,
        "dignity_detail": opt_dignity_det,
        "dig_bala": opt_dig_bala,
        "vargottama": opt_vargottama,
        "gandanta": opt_gandanta,
        # --- future options (UIだけ先行) ---
        # "mrityu_bhaga": opt_mrityu_bhaga,
        # "ashtakavarga": opt_ashtakavarga,
        # "shadbala": opt_shadbala,
        "speed_status": opt_speed_status,

        # ---- Varga ----
        "varga_d9_degree": varga_d9_degree,
        "varga_dignity": varga_dignity,

        # ---- Dasha ----
        "vimshottari": opt_vimshottari,
        # "chara_dasha": opt_chara,  # ← 今後実装予定
    }

    # ★ charts の出力フィルタを適用
    out["charts"] = apply_output_options(out["charts"], output_options)

    # ★ Dasha の ON/OFF
    if not output_options.get("vimshottari", False):
        out.pop("dasha", None)

    # 10) バリデーション → 表示/保存
    out = prune_and_validate(out)
    minimize = bool(st.session_state.get("minimize", True))
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
