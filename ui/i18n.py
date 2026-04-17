# i18n.py
from __future__ import annotations
from typing import Dict, Literal
import streamlit as st

# ---------------------------------------------------------------------------
# 1. 有効な翻訳キーを Literal 型として定義（IDE補完・型チェック用）
# ---------------------------------------------------------------------------
I18nKey = Literal[
    "subtitle", "engine", "model", "ref", "engine_swiss", "model_drik", "ref_lahiri",
    "help.button", "help.button_help", "help.tab.how", "help.tab.about", "help.tab.faq", "help.tab.trouble",
    "help.how.title", "help.how.step1.title", "help.how.step1.body", "help.how.step1.image",
    "help.how.step2.title", "help.how.step2.body", "help.how.step2.note", "help.how.step2.image",
    "help.how.step3.title", "help.how.step3.body", "help.how.step3.image",
    "help.how.output.title", "help.how.output.body",
    "help.about.title", "help.about.body",
    "help.about.philosophy.title", "help.about.philosophy.body",
    "help.about.assumptions.title", "help.about.assumptions.body",
    "help.about.disclaimer",
    "help.faq.title", "help.faq.q1.q", "help.faq.q1.a",
    "help.faq.q2.q", "help.faq.q2.a",
    "help.faq.q3.q", "help.faq.q3.a",
    "help.faq.q4.q", "help.faq.q4.a",
    "help.trouble.title", "help.trouble.checklist",
    "help.trouble.slow.q", "help.trouble.slow.a",
    "help.trouble.large.q", "help.trouble.large.a",
    "help.footer",
    "input_bd", "name", "gender", "choose", "male", "female", "birth", "birth_help",
    "Hr", "Min", "Sec", "geo", "geo_gmap", "gmap", "geo_paste", "geo_help",
    "geo_ph", "geo_clear", "geo_success", "geo_notice_low_conf", "geo_error",
    "lat", "lon", "tz", "tz_help",
    "output_settings", "output_level",
    "preset_desc_basic", "preset_desc_standard", "preset_desc_advanced", "preset_desc_custom",
    "tab_basic", "tab_d1", "tab_varga", "tab_dasha",
    "node_type", "node_mean", "node_true", "ck_mode", "ck_8", "ck_7", "minimize",
    "d1_interactions", "d1_motion", "d1_conditions", "d1_special",
    "chk_nak_lord", "chk_aspects", "chk_conjunctions", "chk_speed_status",
    "chk_combust", "chk_planet_war", "chk_dignity_detail", "chk_dig_bala",
    "chk_vargottama", "chk_gandanta",
    "d1", "d2", "d3", "d4", "d7", "d9",
    "d10", "d12", "d16", "d20", "d24",
    "d27", "d30", "d40", "d45", "d60",
    "varga_op", "varga_d9_deg", "varga_d3d60_deg", "varga_d3d60_dig",
    "vimshottari", "chara_dasha",
    "btn_generate", "preview", "goto_download", "download"
]

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

        # Help
        "help.button": "Help",
        "help.button_help": "使い方・FAQを表示",

        "help.tab.how": "使い方",
        "help.tab.about": "About",
        "help.tab.faq": "FAQ",
        "help.tab.trouble": "困ったとき",

        "help.how.title": "使い方（最短3ステップ）",

        "help.how.step1.title": "1) 出生データを入力",
        "help.how.step1.body": "- 日時を入力\n- 地名 / 緯度経度 / Google Mapsリンクが使用可能",
        "help.how.step1.image": "日時と場所の入力例",

        "help.how.step2.title": "2) 出力プリセットを選択",
        "help.how.step2.body": "- Basic / Standard / Advanced / Custom\n- 迷ったら Standard",
        "help.how.step2.note": "LLM用途では『意味単位』の一貫性が重要です。",
        "help.how.step2.image": "プリセット選択",

        "help.how.step3.title": "3) Generate → JSON取得",
        "help.how.step3.body": "- Generateをクリック\n- JSONをコピーしてLLMへ",
        "help.how.step3.image": "JSON出力例",

        "help.how.output.title": "主な出力内容",
        "help.how.output.body": "- D1 / D9\n- Panchanga\n- Dasha\n- Enrich（解釈補助）",

        "help.about.title": "JyotiSONとは",
        "help.about.body": "JyotiSONはインド占星術の計算結果をLLM向けJSONとして出力するWebアプリです。",

        "help.about.philosophy.title": "設計思想",
        "help.about.philosophy.body": "- 人間可読より機械可読\n- 一貫性と意味保持を最優先",

        "help.about.assumptions.title": "計算前提",
        "help.about.assumptions.body": "- Sidereal / Lahiri\n- Drik Siddhanta\n- Whole Sign",

        "help.about.disclaimer": "本ツールは娯楽・研究用途です。重要判断には使用しないでください。",

        "help.faq.title": "よくある質問",
        "help.faq.q1.q": "地名で座標が取れない",
        "help.faq.q1.a": "Google Mapsの共有リンクか緯度経度を直接入力してください。",

        "help.faq.q2.q": "タイムゾーンが不安",
        "help.faq.q2.a": "出生年のDSTに注意し、必要なら手動指定してください。",

        "help.faq.q3.q": "おすすめプリセットは？",
        "help.faq.q3.a": "最初は Standard を推奨します。",

        "help.faq.q4.q": "LLM向けおすすめプロンプト",
        "help.faq.q4.a": "あなたは熟練のインド占星術アナリストです。以下のJSONを分析してください。",

        "help.trouble.title": "トラブルシューティング",
        "help.trouble.checklist": "1. 日時\n2. タイムゾーン\n3. 緯度経度\n4. プリセット",

        "help.trouble.slow.q": "生成が遅い",
        "help.trouble.slow.a": "Advanced項目を減らすかStandardに戻してください。",

        "help.trouble.large.q": "JSONが大きすぎる",
        "help.trouble.large.a": "出力項目を絞るか分割して使用してください。",

        "help.footer": "Tip: assets/guide_step*.png を置くとスクリーンショットが表示されます。",

        # Input
        "input_bd": "出生情報の入力",
        "name": "名前", "gender": "性別", "choose": "選択...",
        "male": "男性", "female": "女性",
        "birth": "出生日", "birth_help": "YYYY/MM/DD 形式で入力, 時は24時間制",
        "Hr": "時 (24H)", "Min": "分", "Sec": "秒",
        "geo": "出生地", "geo_gmap": "座標取得先：",
        "gmap": "Googleマップ",
        "geo_paste": "Googleマップの座標を貼り付け",
        "geo_help": "地点を右クリックして表示される数値（例: 35.6812, 139.7671）をコピー、  \n"
                    "または Googleマップの共有リンク（maps.app.goo.gl/XXXX）のコピーを  \n"
                    "そのまま貼り付けてください。",
        "geo_ph": "例: 35.6812, 139.7671", "geo_clear": "貼り付けた場所をクリア",
        "geo_success": "座標を認識しました: 緯度 {default_lat} / 経度 {default_lon}",
        "geo_notice_low_conf": "※ 共有リンクから推定した位置です。必要に応じて数値を確認・調整してください。",
        "geo_error": "無効な座標形式です。35.123, 139.456 のような数値を入力してください。",
        "lat": "緯度（北緯+）", "lon": "経度（東経+）",
        "tz": "UTCオフセット",
        "tz_help": "タイムゾーン・夏時間を出生日・緯度経度から自動検出します。  \n"
                   "手動で修正が必要な場合は変更できます。",

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
        "chk_dignity_detail": "品位に友好/中立/敵対をつける",
        "chk_dig_bala": "ディグ・バラ",
        "chk_vargottama": "ヴァルゴッタマ",
        "chk_gandanta": "ガンダーンタ",

        # Varga
        "d1": "D1 Rashi（基本）* 必須",
        "d9": "D9 Navamsa（本質層）",
        "d2": "D2 Hora（財・リソース）",
        "d3": "D3 Drekkana（兄弟姉妹）",
        "d4": "D4 Chaturthamsa（家・不動産）",
        "d7": "D7 Saptamsa（子ども・想像力）",
        "d10": "D10 Dasamsa（キャリア）",
        "d12": "D12 Dwadasamsa（両親・祖先）",
        "d16": "D16 Shodasamsa（乗り物・快適性）",
        "d20": "D20 Vimsamsa（霊性層）",
        "d24": "D24 Siddhamsa（学び・教育）",
        "d27": "D27 Nakshatramsa（闘争力・身体強度）",
        "d30": "D30 Trimshamsa（不運・逆境）",
        "d40": "D40 Khavedamsa（家系的徳・遺産）",
        "d45": "D45 Akshavedamsa（性質・品質）",
        "d60": "D60 Shashtyamsa（カルマ層）",
        "varga_op": "分割図の出力オプション（クリックで展開）",
        "varga_d9_deg": "D9の度数を出力",
        "varga_d3d60_dig": "D1/D9 以外の分割図でも品位を出力する",
        "varga_d3d60_deg": "D1/D9 以外の分割図でサイン内度数を出力（デバッグ用）",

        # Dasha
        "vimshottari": "ヴィムショッタリ・ダシャー",
        "chara_dasha": "チャラ・ダシャー（未実装）",

        # Buttons
        "btn_generate": "AI向けJSONを生成（プレビュー）",
        "preview": "プレビュー（JSON 内容確認）",
        "goto_download": "ダウンロードへ",
        "download": "最小化JSONをダウンロード（{file_name}）",
    },

    "EN": {
        "subtitle": "Jyotish Chart JSON Generator for AI",

        # =========================
        # Help / User Guide (EN)
        # =========================

        "help.button": "Help",
        "help.button_help": "Show usage guide and FAQ",

        "help.tab.how": "How to use",
        "help.tab.about": "About",
        "help.tab.faq": "FAQ",
        "help.tab.trouble": "Troubleshooting",

        # --- How to use ---
        "help.how.title": "How to Use (3 Quick Steps)",

        "help.how.step1.title": "1) Enter Birth Data",
        "help.how.step1.body":
            "- Enter date and time of birth\n"
            "- Location can be provided as:\n"
            "  - Place name\n"
            "  - Latitude / longitude\n"
            "  - Google Maps share link",
        "help.how.step1.image": "Birth date, time, and location input example",

        "help.how.step2.title": "2) Choose an Output Preset",
        "help.how.step2.body":
            "- Select from Basic / Standard / Advanced / Custom\n"
            "- If unsure, start with **Standard**",
        "help.how.step2.note":
            "For LLM usage, consistency by semantic unit is more important than raw volume.",
        "help.how.step2.image": "Output preset selection",

        "help.how.step3.title": "3) Generate → Get JSON",
        "help.how.step3.body":
            "- Click **Generate**\n"
            "- Copy the generated JSON and paste it into your LLM",
        "help.how.step3.image": "Generated JSON output example",

        "help.how.output.title": "Main Output Contents",
        "help.how.output.body":
            "- D1 / D9 charts\n"
            "- Panchanga (Tithi, Nakshatra, etc.)\n"
            "- Vimshottari Dasha\n"
            "- Enrichment data (lords, aspects, dignity, etc.)",

        # --- About ---
        "help.about.title": "What is JyotiSON?",
        "help.about.body":
            "JyotiSON is a web application that generates Jyotish (Vedic astrology) "
            "calculation results as **LLM-friendly structured JSON**.",

        "help.about.philosophy.title": "Design Philosophy",
        "help.about.philosophy.body":
            "- Prioritize machine-readability over human-readable formatting\n"
            "- Preserve semantic meaning rather than visual presentation\n"
            "- Avoid unnecessary verbosity to ensure stable LLM analysis",

        "help.about.assumptions.title": "Calculation Assumptions",
        "help.about.assumptions.body":
            "- Zodiac: Sidereal (Lahiri Ayanamsa)\n"
            "- Calculation model: Drik Siddhanta\n"
            "- House system: Whole Sign",

        "help.about.disclaimer":
            "This tool is intended for research and exploratory use only. "
            "Do not rely on it for medical, legal, financial, or other critical decisions.",

        # --- FAQ ---
        "help.faq.title": "Frequently Asked Questions",

        "help.faq.q1.q": "Location lookup does not work with place names",
        "help.faq.q1.a":
            "Use a Google Maps share link or enter latitude and longitude directly.",

        "help.faq.q2.q": "I'm unsure about the timezone or DST",
        "help.faq.q2.a":
            "Timezone is auto-detected when possible. For historical dates, "
            "please verify daylight saving time and switch to manual mode if needed.",

        "help.faq.q3.q": "Which preset should I use?",
        "help.faq.q3.a":
            "Start with **Standard**. Move to Advanced or Custom only if additional "
            "data is clearly required.",

        "help.faq.q4.q": "Recommended prompt for LLM analysis",
        "help.faq.q4.a":
            "You are an experienced Jyotish analyst. "
            "Analyze the following JyotiSON JSON and explain:\n"
            "(1) personality traits\n"
            "(2) career tendencies\n"
            "(3) relationships\n"
            "(4) overall trends for the next 12 months.\n"
            "Cite relevant JSON keys (e.g., d1.planets, d9, dasha) as evidence.",

        # --- Troubleshooting ---
        "help.trouble.title": "Troubleshooting",

        "help.trouble.checklist":
            "Check the following first:\n"
            "1. Date and time (AM/PM)\n"
            "2. Timezone and daylight saving time\n"
            "3. Latitude / longitude sign (+ / -)\n"
            "4. Output preset settings",

        "help.trouble.slow.q": "Generation is slow",
        "help.trouble.slow.a":
            "Advanced or Custom presets increase computation cost. "
            "Try switching back to Standard and add options gradually.",

        "help.trouble.large.q": "The JSON output is too large for my LLM",
        "help.trouble.large.a":
            "Reduce output options, switch to a lighter preset, or split the JSON "
            "into multiple parts (e.g., charts first, dasha separately).",

        # --- Footer ---
        "help.footer":
            "Tip: Place screenshots as assets/guide_step*.png to display them in this guide.",

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
        "geo": "Birth Place", "geo_gmap": "Get coordinates from ",
        "gmap": "Google Maps",
        "geo_paste": "Paste Google Maps Coordinates",
        "geo_help": "Copy the coordinates shown by right-clicking a location (e.g. 35.6812, 139.7671)  \n"
                    "or a Google Maps share link (maps.app.goo.gl/XXXX), and paste directly.",
        "geo_ph": "e.g. 35.6812, 139.7671", "geo_clear": "Clear pasted location",
        "geo_success": "Coordinates recognized: Latitude {default_lat} / Longitude {default_lon}",
        "geo_notice_low_conf": "Note: This location was inferred from a share link. Please review and adjust if needed.",
        "geo_error": "Invalid coordinate format. Please enter numbers like 35.123, 139.456.",
        "lat": "Latitude (North +)", "lon": "Longitude (East +)",
        "tz": "UTC Offset",
        "tz_help": "Time zone and Daylight Saving Time (DST) are automatically  \n"
                   "detected based on the birth date and coordinates.  \n"
                   "You can manually adjust them if necessary.",

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
        "d2": "D2 Hora (Wealth / Resources)",
        "d3": "D3 Drekkana (Siblings)",
        "d4": "D4 Chaturthamsa (Home/Property)",
        "d7": "D7 Saptamsa (Children)",
        "d10": "D10 Dasamsa (Career)",
        "d12": "D12 Dwadasamsa (Parents/Ancestors)",
        "d16": "D16 Shodasamsa (Vehicles/Comfort)",
        "d20": "D20 Vimsamsa (Spiritual)",
        "d24": "D24 Siddhamsa (Education)",
        "d27": "D27 Nakshatramsa (Strength / Resilience)",
        "d30": "D30 Trimshamsa (Adversity)",
        "d40": "D40 Khavedamsa (Lineage Merit)",
        "d45": "D45 Akshavedamsa (Quality / Nature)",
        "d60": "D60 Shashtyamsa (Karmic)",
        "varga_op": "Divisional Chart Output Options (click to expand)",
        "varga_d9_deg": "Show degrees in D9",
        "varga_d3d60_dig": "Include dignity in charts other than D1/D9",
        "varga_d3d60_deg": "Show degrees in charts other than D1/D9 (debug)",

        # Dasha
        "vimshottari": "Vimshottari Dasha",
        "chara_dasha": "Chara Dasha (future)",

        # Buttons
        "btn_generate": "Generate JSON for AI (Preview)",
        "preview": "Preview (JSON content)",
        "goto_download": "Jump to Download",
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


def t(key: I18nKey | str) -> str:
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
