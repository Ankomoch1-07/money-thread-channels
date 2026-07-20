#!/usr/bin/env python3
"""flavor層：5ch/まとめの「雰囲気(mood)」だけ抽出（翻案専用・ローンチから投入）。

安全設計：まとめサイトの公開RSSを優先（安定・合法配信）。5ch直スクレイプは避ける。
抽出するのは mood（煽り/温度感）のみ。生レス・記事本文の転載は絶対にしない。
best-effort：取得失敗・未設定なら {} を返してスキップ（可用性）。
現状は見出しの温度感をヒューリスティックで拾う。本番はLLMで1〜2文に要約（TODO）。
"""
from __future__ import annotations
from collectors import reference_rss  # まとめRSSも同じRSSパーサで取得

# 見出しから拾う「ノリ」のシグナル語
MOOD_SIGNALS = {
    "乗り遅": "乗り遅れ組の焦り", "まだ間に合": "まだ買えるか論争", "高値": "高値警戒",
    "暴落": "暴落待ち・狼狽", "最高値": "最高値で盛り上がり", "含み益": "含み益自慢",
    "売っちまった": "早売り後悔", "ゴミ": "金否定派の煽り",
}

def collect(sources: list[dict], keywords: list[str]) -> dict:
    """{mood, note} を返す。取得できなければ {}。生データは保持しない。"""
    rss = [s for s in (sources or []) if s.get("type") == "matome_rss" and s.get("url")]
    try:
        items = reference_rss.collect(rss, keywords, 24 * 3)
    except Exception:
        items = []
    if not items:
        return {}
    blob = " ".join((it.get("title") or "") for it in items)
    moods = [v for k, v in MOOD_SIGNALS.items() if k in blob]
    return {
        "mood": "／".join(dict.fromkeys(moods)) or "通常運転",
        "note": "翻案専用。生レス・記事本文の転載は禁止（雰囲気のみ）",
    }

if __name__ == "__main__":
    print("flavor_5ch: import OK（翻案専用・生レス転載禁止）")
