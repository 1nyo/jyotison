# calc/dasha.py
from __future__ import annotations

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, timezone

# ------------------------------------------------------------
# 定数・基本
# ------------------------------------------------------------

# Vimshottari の 9 主（Ketu→Venus→Sun→Moon→Mars→Rahu→Jupiter→Saturn→Mercury）
DASA_CYCLE = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
# 27 ナクシャトラ主（9 主 × 3 周）
NAK_LORD_SEQ = DASA_CYCLE * 3  # 27 個

# 各マハーダシャの年数（合計 120 年）
MAHA_YEARS: Dict[str, int] = {
    "Ke": 7, "Ve": 20, "Su": 6, "Mo": 10, "Ma": 7,
    "Ra": 18, "Ju": 16, "Sa": 19, "Me": 17,
}

# ★ 真太陽恒星年を固定（JH の true sidereal solar year に整合する概算）
SIDEREAL_YEAR_DAYS = 365.25636


# ------------------------------------------------------------
# ユーティリティ
# ------------------------------------------------------------

def _fmt_date(d: datetime) -> str:
    """YYYY-MM-DD のみ（時刻は出さない）"""
    return d.strftime("%Y-%m-%d")


def _tz_from_offset_hours(tz_offset: float) -> timezone:
    """+9.0 等のオフセット（時間）から tzinfo を作る"""
    minutes = int(round(tz_offset * 60))
    return timezone(timedelta(minutes=minutes))


def _nak_index(moon_lon: float) -> int:
    """出生時月黄経（sidereal 0..360）からナクシャトラ index（0..26）"""
    size = 360.0 / 27.0
    return int((moon_lon % 360.0) // size) % 27


def _frac_in_nak(moon_lon: float) -> float:
    """
    ナクシャトラ内の進捗率（左端0→右端1）。
    残り割合は 1 - 進捗率。
    """
    size = 360.0 / 27.0
    pos = (moon_lon % 360.0) % size
    return pos / size


def _cycle_from(lord: str) -> List[str]:
    """DASA_CYCLE を lord 起点に並べ替え（lord, ... の順）"""
    i = DASA_CYCLE.index(lord)
    return DASA_CYCLE[i:] + DASA_CYCLE[:i]


def _add_years(start: datetime, years: float) -> datetime:
    """真恒星年（固定日数）で年数加算"""
    return start + timedelta(days=years * SIDEREAL_YEAR_DAYS)


# ------------------------------------------------------------
# MD（マハーダシャ）だけのコア
# ------------------------------------------------------------

def compute_vimshottari_md(
    birth_dt_local: datetime,
    tz_offset: float,
    moon_abs_long: float,
    *,
    horizon_years: int = 110,  # 出生から +110年で打ち切り
) -> Dict:
    """
    Vimshottari の MD（マハーダシャ）だけを返す版（真恒星年固定・シンプル）。
    返り値:
      {
        "system": "Vimshottari",
        "at_birth": {"maha": <lord>, "remaining_years": <float>},
        "full_sequence_maha": [
          {"lord": "..", "start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
          ...
        ]
      }
    """
    _ = tz_offset  # I/F 互換のため受け取るが、MD 計算そのものでは不使用

    # 1) 出生時のナクシャトラ主
    idx = _nak_index(moon_abs_long)
    maha_at_birth = NAK_LORD_SEQ[idx]

    # 2) 残余年数 = （ナクシャトラ内残割合）×（当該MDの総年数）
    frac = _frac_in_nak(moon_abs_long)        # 進捗 0..1
    remaining_frac = 1.0 - frac               # 残り
    total_years_this_md = MAHA_YEARS[maha_at_birth]
    remaining_years = remaining_frac * total_years_this_md  # ★要点

    # 3) 現行MDの end は birth + remaining_years（保証点）
    md_end_0 = _add_years(birth_dt_local, remaining_years)
    #    start は end - そのMDの総年数
    md_start_0 = _add_years(md_end_0, -total_years_this_md)

    # 4) 以降の MD を horizon まで順次生成
    seq_dt: List[Dict] = []
    seq_dt.append({"lord": maha_at_birth, "start": md_start_0, "end": md_end_0})

    t = md_end_0
    horizon_days = int(horizon_years * SIDEREAL_YEAR_DAYS)
    for lord in _cycle_from(maha_at_birth)[1:]:
        years = MAHA_YEARS[lord]
        end = _add_years(t, years)
        seq_dt.append({"lord": lord, "start": t, "end": end})
        t = end
        if (t - birth_dt_local).days > horizon_days:
            break

    # 5) 文字列化して返す
    seq_out = [
        {"lord": it["lord"], "start": _fmt_date(it["start"]), "end": _fmt_date(it["end"])}
        for it in seq_dt
    ]

    return {
        "system": "Vimshottari",
        "at_birth": {
            "maha": maha_at_birth,
            "remaining_years": round(remaining_years, 4),
        },
        "full_sequence_maha": seq_out,
    }

# ------------------------------------------------------------
# AD（アンタル）を“現在を含む前後3つずつ＝合計7本”で返す（MDごとにまとめる）
# ------------------------------------------------------------

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

def _md_sequence(
    birth_dt: datetime, maha_at_birth: str, remaining_years: float
) -> List[Dict]:
    """
    MD のシーケンス（datetime のまま）。horizon 打ち切りは呼び出し元で行う。
    先頭（出生時点で運行中のMD）は、
      end = birth + remaining_years * SIDEREAL_YEAR_DAYS
      start = end - total_years_this_MD * SIDEREAL_YEAR_DAYS
    以降は順次 total_years を加えていく。
    """
    md_end_0 = _add_years(birth_dt, remaining_years)
    md_start_0 = _add_years(md_end_0, -MAHA_YEARS[maha_at_birth])
    seq = [{"lord": maha_at_birth, "start": md_start_0, "end": md_end_0}]
    t = md_end_0
    for lord in _cycle_from(maha_at_birth)[1:]:
        years = MAHA_YEARS[lord]
        end = _add_years(t, years)
        seq.append({"lord": lord, "start": t, "end": end})
        t = end
    return seq


def _current_md(md_seq: List[Dict], now_dt: datetime) -> Tuple[int, Dict]:
    """現在が属する MD の (index, item) を返す。見つからない場合 (-1, {})."""
    for i, md in enumerate(md_seq):
        if md["start"] <= now_dt < md["end"]:
            return i, md
    return -1, {}


def _antar_seq_for_md(md_lord: str, md_start: datetime, md_end: datetime, md_index: int) -> List[Dict]:
    """
    その MD 期間を AD（9 本）に比例分割して開始日を並べる（終了は使わない）。
    長さ = MD 実期間 × ( sublord_years / 120 )。
    順序 = MD 主 → 以降の順。
    返り値各要素に md_index を持たせ、MDごとグルーピングに利用。
    """
    cycle = DASA_CYCLE
    i0 = cycle.index(md_lord)
    order = cycle[i0:] + cycle[:i0]

    md_days = (md_end - md_start).total_seconds() / 86400.0
    out: List[Dict] = []
    t = md_start
    for sub in order:
        portion = MAHA_YEARS[sub] / 120.0
        dur_days = md_days * portion
        out.append({"lord": sub, "start": t, "md_index": md_index})
        t = t + timedelta(days=dur_days)
    return out


def compute_vimshottari_md_with_context(
    birth_dt_local: datetime,
    tz_offset: float,
    moon_abs_long: float,
    *,
    horizon_years: int = 110,
    now_dt_local: Optional[datetime] = None,
) -> Dict:
    """
    MD（マハーダシャ）＋ current_context（“現在を含む前後3つずつ＝合計7本”の AD）を返す版。
    - 7本は時間的に連続となるよう、前MD末尾 → 現MD → 次MD先頭 を連結したストリームから抜き出す
    - 出力は MD ごとにまとめる：
        "current_sequence": [
          {"maha_lord":"<前MD主>", "antar":[{lord,start,label},...]},
          {"maha_lord":"<現MD主>", "antar":[{lord,start,label},...]},
          （必要なら）{"maha_lord":"<次MD主>", ...}
        ]
    """
    tz = _tz_from_offset_hours(tz_offset)
    if now_dt_local is None:
        now_dt_local = datetime.now(tz)

    # 1) 出生時 MD 主と残余年数
    idx = _nak_index(moon_abs_long)
    maha_at_birth = NAK_LORD_SEQ[idx]
    frac = _frac_in_nak(moon_abs_long)
    remaining_years = (1.0 - frac) * MAHA_YEARS[maha_at_birth]

    # 2) MD の datetime シーケンス
    md_seq_dt = _md_sequence(birth_dt_local, maha_at_birth, remaining_years)

    # 3) horizon で打ち切り（MDの start が horizon 内のものだけ残す）
    horizon_days = int(horizon_years * SIDEREAL_YEAR_DAYS)
    md_seq_dt = [md for md in md_seq_dt if (md["start"] - birth_dt_local).days <= horizon_days]

    # 4) 現在 MD を特定
    i_curr, curr_md = _current_md(md_seq_dt, now_dt_local)
    current_context = None

    if i_curr >= 0:
        # 5) 連続ストリームを作る：前MD(あれば) + 現MD + 次MD(あれば) の AD を連結
        ad_stream: List[Dict] = []
        if i_curr - 1 >= 0:
            prev_md = md_seq_dt[i_curr - 1]
            ad_stream.extend(_antar_seq_for_md(prev_md["lord"], prev_md["start"], prev_md["end"], i_curr - 1))
        ad_stream_curr = _antar_seq_for_md(curr_md["lord"], curr_md["start"], curr_md["end"], i_curr)
        ad_stream.extend(ad_stream_curr)
        next_md = None
        if i_curr + 1 < len(md_seq_dt):
            next_md = md_seq_dt[i_curr + 1]
            ad_stream.extend(_antar_seq_for_md(next_md["lord"], next_md["start"], next_md["end"], i_curr + 1))

        # 6) 現在 AD のインデックス（ad_stream 内）
        ad_idx = 0
        for i in range(len(ad_stream)):
            s = ad_stream[i]["start"]
            e = ad_stream[i + 1]["start"] if i + 1 < len(ad_stream) else (
                md_seq_dt[ad_stream[i]["md_index"]]["end"]
            )
            if s <= now_dt_local < e:
                ad_idx = i
                break

        # 7) current を中心に前後3つ（最大7本）を連続に抜き出す
        start_idx = max(0, ad_idx - 3)
        end_idx   = min(len(ad_stream) - 1, ad_idx + 3)
        picked = ad_stream[start_idx : end_idx + 1]

        # 8) ラベル付け（連続の相対位置で決める：-3..+3 → past_3..future_3）
        labels = ["past_3", "past_2", "past_1", "current", "future_1", "future_2", "future_3"]
        rel_current = ad_idx - start_idx  # picked 内での current 位置
        labeled: List[Dict] = []
        for k, it in enumerate(picked):
            rel = k - rel_current
            # 範囲内だけ（念のため）
            if -3 <= rel <= 3:
                labeled.append({
                    "lord": it["lord"],
                    "start": it["start"],
                    "label": labels[rel + 3],
                    "md_index": it["md_index"],
                })

        # 9) MDごとにまとめる（時間順の picked から md_index ごとにグループ化）
        #    出力：[{ "maha_lord": "...", "antar":[{lord,start,label},...] }, ...]
        groups: Dict[int, List[Dict]] = {}
        order_md_indices: List[int] = []
        for it in labeled:
            mid = it["md_index"]
            if mid not in groups:
                groups[mid] = []
                order_md_indices.append(mid)
            groups[mid].append({"lord": it["lord"], "start": it["start"], "label": it["label"]})

        current_sequence: List[Dict] = []
        for mid in order_md_indices:
            md = md_seq_dt[mid]
            antar_items = [
                {"lord": x["lord"], "start": _fmt_date(x["start"]), "label": x["label"]}
                for x in groups[mid]
            ]
            current_sequence.append({
                "maha_lord": md["lord"],
                "antar": antar_items
            })

        # 10) まとめた current_context を返す
        current_context = {
            "current_maha": curr_md["lord"],
            "current_antar": next((x["lord"] for x in labeled if x["label"] == "current"), None),
            "current_sequence": current_sequence
        }

    # 11) MD（文字列化）—MDコンテキスト付きの戻り値を統一
    seq_out = [
        {"lord": it["lord"], "start": _fmt_date(it["start"]), "end": _fmt_date(it["end"])}
        for it in md_seq_dt
    ]

    return {
        "system": "Vimshottari",
        "at_birth": {
            "maha": maha_at_birth,
            "remaining_years": round(remaining_years, 4),
        },
        "full_sequence_maha": seq_out,
        "current_context": current_context,
    }
