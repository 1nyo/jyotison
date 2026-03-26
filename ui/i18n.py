# i18n.py
from __future__ import annotations
from typing import Dict
import streamlit as st

# ---- 翻訳辞書（ここに LANG_DICT を移動）----
LANG_DICT: Dict[str, Dict[str, str]] = {

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
        "geo_help": "地点を右クリックして表示される数値（例: 35.6812, 139.7671）をコピー、または Googleマップの共有リンク（maps.app.goo.gl/XXXX）をそのまま貼り付けできます。",
        "geo_ph": "例: 35.6812, 139.7671", "geo_clear": "貼り付けた場所をクリア",
        "geo_success": "座標を認識しました: 緯度 {default_lat} / 経度 {default_lon}",
        "geo_notice_low_conf": "※ 共有リンクから推定した位置です。必要に応じて数値を確認・調整してください。",
        "geo_error": "無効な座標形式です。35.123, 139.456 のような数値を入力してください。",
        "lat": "緯度（北緯+）", "lon": "経度（東経+）",
        "tz": "UTCオフセット", "tz_auto": "（自動認識）",
        "tz_help": "タイムゾーン・夏時間を出生日・緯度経度から自動検出します。手動で修正が必要な場合は変更できます。",

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
        "geo_help": "Copy the coordinates shown by right-clicking a location (e.g. 35.6812, 139.7671), or paste a Google Maps share link (maps.app.goo.gl/XXXX) directly.",
        "geo_ph": "e.g. 35.6812, 139.7671", "geo_clear": "Clear pasted location",
        "geo_success": "Coordinates recognized: Latitude {default_lat} / Longitude {default_lon}",
        "geo_notice_low_conf": "Note: This location was inferred from a share link. Please review and adjust if needed.",
        "geo_error": "Invalid coordinate format. Please enter numbers like 35.123, 139.456.",
        "lat": "Latitude (North +)", "lon": "Longitude (East +)",
        "tz": "UTC Offset", "tz_auto": "(Auto-detected)",
        "tz_help": "Time zone and Daylight Saving Time (DST) are automatically detected based on the birth date and coordinates. You can manually adjust them if necessary.",

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

SUPPORTED_LANGS = ("EN", "JP")


def validate_lang_dict(strict: bool = False) -> None:
    """
    JP/EN 間のキー差分を検知。
    strict=True の場合は例外を投げて起動時に落とす（開発向け）。
    strict=False は st.warning を出す（運用向け）。
    """
    en = set(LANG_DICT.get("EN", {}).keys())
    jp = set(LANG_DICT.get("JP", {}).keys())
    missing_in_jp = sorted(en - jp)
    missing_in_en = sorted(jp - en)

    if not missing_in_jp and not missing_in_en:
        return

    msg = []
    if missing_in_jp:
        msg.append(f"Missing keys in JP: {missing_in_jp}")
    if missing_in_en:
        msg.append(f"Missing keys in EN: {missing_in_en}")

    text = " / ".join(msg)
    if strict:
        raise KeyError(text)
    else:
        # streamlit 実行中だけ警告（辞書だけ import する用途もあるので例外にしない）
        try:
            st.warning(f"[i18n] {text}")
        except Exception:
            # streamlit 未初期化環境で import されても壊れないように
            pass


def t(key: str) -> str:
    """
    セッションの lang を見て文字列を返す。
    - lang が不正なら EN
    - key が無ければ EN -> key -> '[[key]]' の順でフォールバック
    """
    lang = st.session_state.get("lang", "EN")
    if lang not in SUPPORTED_LANGS:
        lang = "EN"

    # まず選択言語を試す
    d = LANG_DICT.get(lang, {})
    if key in d:
        return d[key]

    # 次に EN を試す
    en = LANG_DICT.get("EN", {})
    if key in en:
        return en[key]

    # 最後はキーを可視化して落ちないように
    return f"[[{key}]]"