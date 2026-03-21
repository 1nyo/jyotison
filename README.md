![JyotiSON](jyotison.png)

# JyotiSON

**JyotiSON** は、LLM（大規模言語モデル）に正確なクンダリー（インド占星術チャート）を読ませるための  
**AI解析専用・ヴェーダ占星術チャートJSON生成ツール**です。

https://jyotison.streamlit.app/

出生情報から、解釈の揺れや欠落を極力減らした構造化JSONを生成することで、  
**AIによるヴェーダ占星術リーディングの精度を大きく向上させる**ことを目的としています。

---

## できること

- 出生情報（日時・場所）から **サイデリアル（Lahiri）** のクンダリーを計算
- D1 / D9 を中心に、必要に応じて各種分割図（D3〜D60）を生成
- ナクシャトラ、品位、逆行、コンバスト、チャラ・カーラカ、アルーダ等を含む
- **LLM解析用途に最適化されたJSON形式**で出力
- JSONは人間向けではなく、**AIが誤読しにくい構造と粒度**を優先

---

## 想定用途

- ChatGPT / Claude などの LLM にクンダリーJSONを直接渡して解析させる
- 占星術AIアプリ・ボットの入力データ生成
- 占星術リーディング実験・検証用データ作成

※ 人間が読むためのチャート表示ツールではありません。

---

## 計算仕様（要点）

- Ephemeris: **Swiss Ephemeris**
- Zodiac: **Sidereal**
- Ayanamsa: **Lahiri**
- Calculation model: **Drik**
- House system: **Whole Sign**
- Nodes: Mean / True 切替可

---

## 出力例（抜粋）

```json
{
  "schema": "kundali_llm_v1",
  "generator": {
    "tool": "JyotiSON",
    "purpose": "LLM_vedic_astrology_analysis"
  },
  "birth_data": {
    "birth": "1990-01-01T12:00:00+09:00",
    "latitude": 35.68,
    "longitude": 139.77
  },
  "charts": {
    "D1": { "...": "..." },
    "D9": { "...": "..." }
  },
  "dasha": {
    "system": "Vimshottari"
  }
}
