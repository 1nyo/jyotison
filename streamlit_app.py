# streamlit_app.py
import json
from timezonefinder import TimezoneFinder
from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import Optional, cast, Literal
import re

import streamlit as st

# ---- calc imports ----
from calc import (
    julday_utc, calc_planet, calc_asc_long,
    prune_and_validate, pretty_json_inline_lists
)
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
        # Header
        "subtitle": "AI向けインド占星術チャートデータ生成ツール",

        # Engine
        "engine": "エンジン", "model": "計算モデル", "ref": "準拠",
        "engine_swiss": "Swiss Ephemeris",
        "model_drik": "Drik（観測準拠）",
        "ref_lahiri": "Lahiri（サイデリアル）",

        # Input
        "input_bd": "出生情報の入力",
        "name": "名前", "gender": "性別", "choose": "選択...",
        "male": "男性", "female": "女性",
        "birth": "出生日", "birth_help": "YYYY/MM/DD 形式で入力, 時は24時間制",
        "Hr": "時 (24H)", "Min": "分", "Sec": "秒",
        "geo": "出生地", "geo_gmap": "（初期値は東京）座標取得先（推奨）：",
        "gmap": "Googleマップ",
        "geo_paste": ":material/location_on: Googleマップの座標を貼り付け",
        "geo_help": "地点を右クリックして出現した数値をクリックしてコピーし、そのままここに貼り付けてください",
        "geo_ph": "例: 35.6812, 139.7671", "geo_clear": "貼り付けた場所をクリア",
        "geo_success": "座標を認識しました: 緯度 {default_lat} / 経度 {default_lon}",
        "geo_error": "無効な座標形式です。35.123, 139.456 のような数値を入力してください。",
        "lat": "緯度（北緯+）", "lon": "経度（東経+）",
        "tz": "UTCオフセット", "tz_auto": "（自動認識）",
        "tz_help": "手動で修正が必要な場合は貼り付け座標をクリアしてください。",

        # Output Settings
        "output_settings": "出力方法の設定",
        "output_level": "出力レベル（推奨設定セット）",

        # Output Level descriptions
        "preset_desc_basic": "🔹 Basic（軽量）: 最小限の補助線だけでAIの解釈の自由度を残す構成。",
        "preset_desc_standard": "🔷 Standard（推奨）: D1/D9と主要補助線を揃えたバランス構成。",
        "preset_desc_advanced": "🔶 Advanced（完全版）: 全補助線・分割図を含むフルスペック構成。",
        "preset_desc_custom": "✳ Custom（自由調整）: 現在の構成はプリセットと一致していません。",

        # Tabs
        "tab_basic": "基本設定",
        "tab_d1": "D1 詳細",
        "tab_varga": "分割図",
        "tab_dasha": "ダシャー",

        # Node Type
        "node_type": "ノードの計算",
        "node_mean": "Mean Node（平均）",
        "node_true": "True Node（真）",

        # Chara Karaka
        "ck_mode": "チャラ・カーラカ",
        "ck_8": "8（Rahu含む）",
        "ck_7": "7（Rahu除外）",

        # Minimize JSON output
        "minimize": "JSON出力を最小化（スペース・改行なし）",

        # D1 detail groups
        "d1_interactions": "関係性",
        "d1_motion": "惑星運動",
        "d1_conditions": "惑星状態",
        "d1_special": "特殊配置",

        # D1 detail options
        "chk_nak_lord": "ナクシャトラロード",
        "chk_aspects": "アスペクト（グラハ・ドリシュティ）",
        "chk_conjunctions": "コンジャンクション",
        "chk_speed_status": "速度の特異値（高速/低速/停止）",
        "chk_combust": "コンバスト",
        "chk_planet_war": "惑星戦争（グラハ・ユッダ）",
        "chk_dignity_detail": "品位に有効/中立/敵対をつける",
        "chk_dig_bala": "ディグ・バラ",
        "chk_vargottama": "ヴァルゴッタマ",
        "chk_gandanta": "ガンダーンタ",

        # Varga
        "d1": "D1 Rashi（基本）* 必須",
        "d9": "D9 Navamsa（本質層）",
        "d3": "D3 Drekkana（兄弟姉妹）",
        "d4": "D4 Chaturthamsa（家・不動産）",
        "d7": "D7 Saptamsa（子ども・想像力）",
        "d10": "D10 Dasamsa（キャリア）",
        "d12": "D12 Dwadasamsa（両親・祖先）",
        "d16": "D16 Shodasamsa（乗り物・快適性）",
        "d20": "D20 Vimsamsa（霊性層）",
        "d24": "D24 Siddhamsa（学び・教育）",
        "d30": "D30 Trimshamsa（不運・逆境）",
        "d60": "D60 Shashtyamsa（カルマ層）",
        "varga_op": "分割図の出力オプション（クリックで展開）",
        "varga_d9_deg": "D9の度数を出力",
        "varga_d3d60_dig": "D1/D9 以外の分割図で品位（高揚/減衰のみ）を出力する",

        # Dasha
        "vimshottari": "ヴィムショッタリ・ダシャー",
        "chara_dasha": "チャラ・ダシャー（未実装）",

        # Buttons
        "btn_generate": "AI向けJSONを生成（プレビュー）",
        "preview": "プレビュー（JSON 内容確認）",
        "download": "最小化JSONをダウンロード（{file_name}）",
    },

    "EN": {
        "subtitle": "Jyotish Chart JSON Generator for AI",

        # Engine
        "engine": "Engine", "model": "Model", "ref": "Reference",
        "engine_swiss": "Swiss Ephemeris",
        "model_drik": "Drik (Observational)",
        "ref_lahiri": "Lahiri (Sidereal)",

        # Input
        "input_bd": "Input Birth Details",
        "name": "Name", "gender": "Gender", "choose": "Choose...",
        "male": "Male", "female": "Female",
        "birth": "Birth Date", "birth_help": "Enter date in YYYY/MM/DD format, time in 24-hour format",
        "Hr": "Hour (24H)", "Min": "Minute", "Sec": "Second",
        "geo": "Birth Place", "geo_gmap": "(Default: Tokyo) Get coordinates from ",
        "gmap": "Google Maps",
        "geo_paste": ":material/location_on: Paste Google Map Coordinates",
        "geo_help": "Copy the numbers that appear when you right-click on a location and paste them here",
        "geo_ph": "e.g. 35.6812, 139.7671", "geo_clear": "Clear pasted location",
        "geo_success": "Coordinates recognized: Latitude {default_lat} / Longitude {default_lon}",
        "geo_error": "Invalid coordinate format. Please enter numbers like 35.123, 139.456.",
        "lat": "Latitude (North +)", "lon": "Longitude (East +)",
        "tz": "UTC Offset", "tz_auto": "(Auto-detected)",
        "tz_help": "If you need to adjust manually, please clear the pasted coordinates.",

        # Output
        "output_settings": "Output Settings",
        "output_level": "Output Level (Recommended Preset Sets)",

        # Output Level descriptions
        "preset_desc_basic": "🔹 Basic: Lightweight setting allowing greater interpretive freedom.",
        "preset_desc_standard": "🔷 Standard (Recommended): Balanced configuration with D1/D9 and key supportive lines.",
        "preset_desc_advanced": "🔶 Advanced (Full): Full specification including all supportive lines and divisional charts.",
        "preset_desc_custom": "✳ Custom: Current configuration does not match any preset.",

        # Tabs
        "tab_basic": "Basic Settings",
        "tab_d1": "D1 Details",
        "tab_varga": "Divisional Charts",
        "tab_dasha": "Dashas",

        # Node Type
        "node_type": "Node Calculation",
        "node_mean": "Mean Node",
        "node_true": "True Node",

        # Chara Karaka
        "ck_mode": "Chara Karaka",
        "ck_8": "8 (Including Rahu)",
        "ck_7": "7 (Excluding Rahu)",

        # Minimize JSON output
        "minimize": "Minimize JSON output (no spaces/newlines)",

        # D1 detail groups
        "d1_interactions": "Interactions",
        "d1_motion": "Planet Motion",
        "d1_conditions": "Planet Conditions",
        "d1_special": "Special Positions",

        # D1 detail options
        "chk_nak_lord": "Nakshatra Lord",
        "chk_aspects": "Aspects to Signs",
        "chk_conjunctions": "Conjunctions",
        "chk_speed_status": "Speed Status (fast/slow/station)",
        "chk_combust": "Combust",
        "chk_planet_war": "Planetary War",
        "chk_dignity_detail": "Dignity (Friendly/Neutral/Enemy)",
        "chk_dig_bala": "Dig Bala",
        "chk_vargottama": "Vargottama",
        "chk_gandanta": "Gandanta",

        # Varga
        "d1": "D1 Rashi (Basic) * Required",
        "d9": "D9 Navamsa (Essence)",
        "d3": "D3 Drekkana (Siblings)",
        "d4": "D4 Chaturthamsa (Home/Property)",
        "d7": "D7 Saptamsa (Children)",
        "d10": "D10 Dasamsa (Career)",
        "d12": "D12 Dwadasamsa (Parents/Ancestors)",
        "d16": "D16 Shodasamsa (Vehicles/Comfort)",
        "d20": "D20 Vimsamsa (Spiritual)",
        "d24": "D24 Siddhamsa (Education)",
        "d30": "D30 Trimshamsa (Adversity)",
        "d60": "D60 Shashtyamsa (Karmic)",
        "varga_op": "Divisional Chart Output Options (click to expand)",
        "varga_d9_deg": "Show degrees in D9",
        "varga_d3d60_dig": "Include dignity (only exaltation/debilitation) for non-D1/D9 charts",

        # Dasha
        "vimshottari": "Vimshottari Dasha",
        "chara_dasha": "Chara Dasha (future)",

        # Buttons
        "btn_generate": "Generate JSON for AI (Preview)",
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

# ------------------------------------------------------------
# Timezone auto-detect (cached + compute only when needed)
# ------------------------------------------------------------

@st.cache_resource
def _get_tz_finder() -> TimezoneFinder:
    """TimezoneFinder は初期化が重いので 1 セッションで使い回す。"""
    return TimezoneFinder()

@st.cache_data(show_spinner=False)
def _tz_name_from_latlon_cached(lat4: float, lon4: float) -> str | None:
    """
    (lat, lon) -> tz_name をキャッシュ。
    入力の微小変化でキャッシュが無駄に増えないよう、呼び出し側で round する。
    """
    tf = _get_tz_finder()
    return tf.timezone_at(lat=lat4, lng=lon4)

def get_tz_name(lat: float, lon: float) -> str | None:
    """外部公開用：丸めてからキャッシュ関数へ。"""
    return _tz_name_from_latlon_cached(round(lat, 4), round(lon, 4))

def get_utc_offset_hours(tz_name: str, dt: datetime) -> float | None:
    """tz_name と dt から offset(hours) を返す。取れない場合 None。"""
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        return None

    offset_td = dt.astimezone(tz).utcoffset()
    if offset_td is None:
        return None
    return offset_td.total_seconds() / 3600.0

def recompute_tz_if_dirty(birth_dt: datetime) -> None:
    """
    tz_dirty が True の時だけ timezonefinder を呼び、
    tz_name / tz(UTC offset) を session_state に更新する。
    """
    if not st.session_state.get("tz_dirty", True):
        return

    lat = float(st.session_state.get("lat", 0.0))
    lon = float(st.session_state.get("lon", 0.0))

    tz_name = get_tz_name(lat, lon)
    st.session_state["tz_name"] = tz_name or "Unknown"
    st.session_state["tz_dst"] = None  # 初期化

    if tz_name:
        try:
            tz = ZoneInfo(tz_name)
            aware_dt = birth_dt.astimezone(tz)

            offset_td = aware_dt.utcoffset()
            if offset_td is not None:
                st.session_state["tz"] = offset_td.total_seconds() / 3600

            # DST 判定
            dst_td = aware_dt.dst()
            if dst_td is not None and dst_td.total_seconds() > 0:
                st.session_state["tz_dst"] = True
            else:
                st.session_state["tz_dst"] = False
            
            # 自動計算が走ったら Auto に戻す
            st.session_state["tz_mode"] = "auto"

        except Exception:
            pass
    # 計算済みにする（以後、lat/lon が変わるまで再計算しない）
    st.session_state["tz_dirty"] = False

def mark_tz_dirty() -> None:
    """Birth D/H/M/S, lat/lon が変わったら True にするための on_change 用。"""
    st.session_state["tz_dirty"] = True

def clear_geo_paste():
    # 貼り付け欄をクリア
    st.session_state["geo_paste"] = ""

    # クリアしたら「自動貼付モード」を解除したいなら dirty を落とす
    # ※この挙動は好み：手動編集に戻したいなら False が自然
    st.session_state["tz_dirty"] = False

def on_tz_manual_change():
    # ユーザーが UTC オフセットを手動変更した
    st.session_state["tz_mode"] = "manual"

# -------------------------------------------------------
# Output Presets (Basic / Standard / Advanced / Custom)
# -------------------------------------------------------

# プリセットが制御するキー（VD1 詳細 + arga + Varga 出力）
PRESET_KEYS = [
    # D1 output details
    "opt_nak_lord", "opt_aspects", "opt_conjunctions", "opt_speed_status",
    "opt_dig_bala", "opt_combust", "opt_planet_war", "opt_dignity_det",
    "opt_vargottama", "opt_gandanta",

    # Varga includes
    "include_d1", "include_d3", "include_d4", "include_d7", "include_d9",
    "include_d10", "include_d12", "include_d16", "include_d20",
    "include_d24", "include_d30", "include_d60",

    # Varga output options
    "varga_d9_degree", "varga_dignity",
]

PRESETS: dict[str, dict[str, bool]] = {
    "Basic": {
        # --- D1 Details ---
        "opt_nak_lord": False,
        "opt_aspects": False,
        "opt_conjunctions": False,
        "opt_speed_status": False,
        "opt_dig_bala": False,
        "opt_combust": True,        # ← ここだけ ON（あなたの方針を踏襲）
        "opt_planet_war": False,
        "opt_dignity_det": False,
        "opt_vargottama": False,
        "opt_gandanta": False,

        # --- Varga ---
        "include_d1": True,
        "include_d9": True,
        "include_d3": False,
        "include_d4": False,
        "include_d7": False,
        "include_d10": False,
        "include_d12": False,
        "include_d16": False,
        "include_d20": False,
        "include_d24": False,
        "include_d30": False,
        "include_d60": False,

        # --- Varga Output ---
        "varga_d9_degree": False,
        "varga_dignity": False,
    },

    "Standard": {
        # --- D1 Details ---
        "opt_nak_lord": True,
        "opt_aspects": True,
        "opt_conjunctions": True,
        "opt_speed_status": False,
        "opt_dig_bala": False,
        "opt_combust": True,
        "opt_planet_war": False,
        "opt_dignity_det": True,
        "opt_vargottama": True,
        "opt_gandanta": True,

        # --- Varga ---
        "include_d1": True,
        "include_d9": True,
        "include_d10": True,
        "include_d20": True,
        "include_d60": True,
        "include_d3": False,
        "include_d4": False,
        "include_d7": False,
        "include_d12": False,
        "include_d16": False,
        "include_d24": False,
        "include_d30": False,

        # --- Varga Output ---
        "varga_d9_degree": True,
        "varga_dignity": True,
    },

    "Advanced": {
        # 全部 ON（PRESET_KEYS 全部 True）
        **{k: True for k in PRESET_KEYS},
    },
}

# 現在の設定からプリセット名を推定する（完全一致のみ）
def _detect_preset_from_state() -> str:
    current = {k: bool(st.session_state.get(k, False)) for k in PRESET_KEYS}
    for name, profile in PRESETS.items():
        if current == profile:
            return name
    return "Custom"


def apply_preset_to_session(preset_name: str) -> None:
    profile = PRESETS.get(preset_name)
    if not profile:
        return
    for key, val in profile.items():
        st.session_state[key] = val


# --- Output Level UI 用の状態管理 ---
# 実際に有効なプロファイル（Basic / Standard / Advanced / Custom）
st.session_state.setdefault("output_profile", "Standard")
# スライダーの位置（Basic / Standard / Advanced）
st.session_state.setdefault("output_level", st.session_state["output_profile"])
# Custom 状態かどうか
st.session_state.setdefault("is_custom", False)

# 初回だけ Standard プリセットを適用（旧ラジオと同じ挙動）
if "preset_initialized" not in st.session_state:
    apply_preset_to_session(st.session_state["output_profile"])
    st.session_state["preset_initialized"] = True


def on_preset_slider_change() -> None:
    """
    スライダーの値が変わったときに呼ばれる。
    - Basic / Standard / Advanced を選んだ → そのプリセットを適用
    - Custom 状態を解除
    """
    new_level = st.session_state.get("output_level", "Standard")
    # プリセット適用
    apply_preset_to_session(new_level)
    # 実際のプロファイルを更新
    st.session_state["output_profile"] = new_level
    # Custom 状態解除
    st.session_state["is_custom"] = False


def on_manual_option_changed() -> None:
    """
    何かのチェックボックスが手動で変更された時に呼ばれる。
    - Basic / Standard / Advanced のどれかと完全一致 → そのプリセット名に戻す（Custom解除）
    - どれとも一致しない → Custom モードに入る
    """
    detected = _detect_preset_from_state()

    if detected in ("Basic", "Standard", "Advanced"):
        # どれかのプリセットと完全一致 → そのプリセットモードに戻す
        st.session_state["output_profile"] = detected
        st.session_state["output_level"] = detected   # スライダーも同期
        st.session_state["is_custom"] = False
    else:
        # どれとも一致しない → Custom
        st.session_state["output_profile"] = "Custom"
        st.session_state["is_custom"] = True


# =======================================================
# 2) ページ上部の余白/CSS・ヘッダー（EN/JP 切り替えもここ）
# =======================================================
st.markdown("<style>.block-container {padding-top: 2rem;}</style>", unsafe_allow_html=True)

st.markdown(
    """
    <style>
    .header-container {text-align: center; padding: 0 0 1.5rem 0; font-family: 'Inter', 'sans-serif';}
    .logo-text {font-size: 4rem; font-weight: 800; letter-spacing: -2px; margin-bottom: 0; line-height: 1;}
    .yoti {opacity: 0.5; font-weight: 500; letter-spacing: -4px; padding: 0 2px;}
    .version-text { font-size: 1rem; vertical-align: super; opacity: 0.5; margin-left: 2px; position: relative; top: -0.8rem; font-weight: 400; letter-spacing: 0; }
    .subtitle-text {font-size: 1rem; font-weight: 500; letter-spacing: 2px; text-transform: uppercase;
        opacity: 0.7; margin-top: 0.9rem;}
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

    # ③ ここで「先に」貼り付けを処理して lat/lon を session_state に反映する
    #    ※ lat/lon ウィジェットを作る前なので Streamlit に怒られない
    if geo_paste:
        res = parse_latlon_any(geo_paste)
        if res:
            pasted_lat, pasted_lon = res
            st.session_state["lat"] = pasted_lat
            st.session_state["lon"] = pasted_lon
            st.session_state["tz_dirty"] = True
            geo_msg.success(t("geo_success").format(default_lat=pasted_lat, default_lon=pasted_lon))
        else:
            geo_msg.error(t("geo_error"))
    else:
        geo_msg.empty()

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
            on_change=mark_tz_dirty,
        )

    with g4:
        geo_lon = st.number_input(
            t("lon"),
            min_value=-180.0,
            max_value=180.0,
            format="%.5f",
            key="lon",
            on_change=mark_tz_dirty,
        )


    # tz 自動計算（ウィジェット生成前）
    birth_dt = datetime(
        year=birth_date.year,
        month=birth_date.month,
        day=birth_date.day,
        hour=h, minute=m, second=s
    )
    recompute_tz_if_dirty(birth_dt)

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
        tz_dst = st.session_state.get("tz_dst")
        tz_mode = st.session_state.get("tz_mode", "auto")

        if tz_dst is True:
            tz_suffix = "DST"
        elif tz_dst is False:
            tz_suffix = "Standard"
        else:
            tz_suffix = "Unknown"
        mode_badge = "Auto" if tz_mode == "auto" else "Manual"
        icon = ":material/check:" if tz_mode == "auto" else ":material/edit:"
        # HTMLでスタイルを当てて表示（小さめの文字でグレーアウト）
        st.markdown(
            f"<span style='font-size:0.85rem; color:gray; top: 0.5rem; position: relative;'>"
            f"{icon} Timezone: <b>{tz_name}</b> ({tz_suffix}) [{mode_badge}]"
            f"</span>",
            unsafe_allow_html=True,
        )


    # 性別コード（内部値から変換）
    GENDER_MAP = {"male": "Male", "female": "Female"}
    gender_code = GENDER_MAP.get(st.session_state["gender"])  # NoneならNone


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
    if st.session_state.get("is_custom", False):
        current_profile = "Custom"
    else:
        current_profile = st.session_state.get(
            "output_profile",
            st.session_state.get("output_level", "Standard"),
        )

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
# ダシャータブ（futureは disabled）
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

def apply_output_options(charts: dict, opt: dict) -> dict:
    import copy
    charts = copy.deepcopy(charts)

    # -------------------------------
    # D1（planets + derived）
    # -------------------------------
    d1 = charts.get("D1")
    if isinstance(d1, dict):
        # ----- D1 Asc -----
        asc = d1.get("Asc")
        if isinstance(asc, dict):
            if not opt.get("nakshatra_lord", False):
                if isinstance(asc.get("nakshatra"), dict):
                    asc["nakshatra"].pop("lord", None)

        # ----- planets -----
        if isinstance(d1.get("planets"), dict):
            for p, rec in d1["planets"].items():
                if not isinstance(rec, dict):
                    continue

                # planets.* の処理（既存のまま）
                if not opt.get("nakshatra_lord", False):
                    if isinstance(rec.get("nakshatra"), dict):
                        rec["nakshatra"].pop("lord", None)

                if not opt.get("aspects", False):
                    rec.pop("aspects_to_sign", None)

                if not opt.get("conjunctions", False):
                    rec.pop("occupancy_in_sign", None)

                if not opt.get("combust", False):
                    rec.pop("combust", None)

                if not opt.get("planet_war", False):
                    rec.pop("planet_war", None)
                
                if not opt.get("dignity_detail", False):
                    dignity = rec.get("dignity")
                    if isinstance(dignity, str):
                        # 残したいものだけ whitelist
                        KEEP_DIGNITIES = {"exalted", "debilitated", "moolatrikona", "owned"}
                        if dignity not in KEEP_DIGNITIES:
                            rec.pop("dignity", None)

                if not opt.get("dig_bala", False):
                    rec.pop("dig_bala", None)

                if not opt.get("vargottama", False):
                    rec.pop("vargottama", None)

                if not opt.get("gandanta", False):
                    rec.pop("gandanta", None)

                if not opt.get("speed_status", False):
                    rec.pop("speed", None)

        # ----- derived -----
        d_derived = d1.get("derived")
        if isinstance(d_derived, dict):

            if not opt.get("dig_bala", False):
                d_derived.pop("dig_bala", None)

            if not opt.get("vargottama", False):
                d_derived.pop("vargottama", None)

            if not opt.get("gandanta", False):
                d_derived.pop("gandanta", None)

            if not opt.get("aspects", False):
                d_derived.pop("aspects_to_sign", None)

            if not opt.get("conjunctions", False):
                d_derived.pop("occupancy_in_sign", None)

            if not opt.get("combust", False):
                d_derived.pop("combust", None)

            if not opt.get("planet_war", False):
                d_derived.pop("planetary_war", None)

            # 将来的にON/OFFするなら opt_lordship を追加
            # 今は常に残す
            # if not opt.get("lordship", False):
            #     d_derived.pop("lordship_to_houses", None)

    # -------------------------------
    # D9
    # -------------------------------
    d9 = charts.get("D9")
    if isinstance(d9, dict):
        # --- D9 Asc ---
        if isinstance(d9.get("Asc"), dict):
            if not opt.get("varga_d9_degree", False):
                d9["Asc"].pop("degree", None)
        # planets の degree 削除
        if isinstance(d9.get("planets"), dict):
            if not opt.get("varga_d9_degree", False):
                for p, rec in d9["planets"].items():
                    rec.pop("degree", None)

    # -------------------------------
    # D3〜D60
    # -------------------------------
    for cname, chart in charts.items():
        if cname in ("D1", "D9"):
            continue
        if not isinstance(chart, dict):
            continue

        if not opt.get("varga_dignity", False):
            if isinstance(chart.get("planets"), dict):
                for p, rec in chart["planets"].items():
                    rec.pop("dignity", None)

    return charts

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
    apply_ordering_to_chart(cast(dict, vargas.get("D1")))
    apply_ordering_to_chart(cast(dict, vargas.get("D9")))
    apply_ordering_to_chart(cast(dict, vargas.get("D3")))
    apply_ordering_to_chart(cast(dict, vargas.get("D4")))
    apply_ordering_to_chart(cast(dict, vargas.get("D7")))
    apply_ordering_to_chart(cast(dict, vargas.get("D10")))
    apply_ordering_to_chart(cast(dict, vargas.get("D12")))
    apply_ordering_to_chart(cast(dict, vargas.get("D16")))
    apply_ordering_to_chart(cast(dict, vargas.get("D20")))
    apply_ordering_to_chart(cast(dict, vargas.get("D24")))
    apply_ordering_to_chart(cast(dict, vargas.get("D30")))
    apply_ordering_to_chart(cast(dict, vargas.get("D60")))
    
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
            "version": "1.1",
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
