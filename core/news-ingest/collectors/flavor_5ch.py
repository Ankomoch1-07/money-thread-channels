#!/usr/bin/env python3
"""flavor層：5ch/まとめの「雰囲気(mood)」だけ抽出（翻案専用）。

★ローンチから投入する層。ただし安全設計を厳守：
- まとめサイトの公開RSSを優先（取得が安定・合法的に配信されている）
- 5ch を使う場合も read.cgi を低頻度＋User-Agent配慮＋robots遵守
- 抽出するのは mood（煽り/温度感）のみ。生レス・記事本文の転載は絶対にしない
戻り値は {mood, note}（ingest.json .flavor）。取得失敗は best-effort でスキップ（可用性）。
"""
from __future__ import annotations

def collect(sources: list[dict], keywords: list[str]) -> dict:
    """{mood, note} を返す（TODO: まとめRSS取得→LLMで雰囲気要約）。"""
    raise NotImplementedError(
        "まとめRSS優先で取得→本文は捨て、話題の温度感だけをLLMで1〜2文に要約。生レス転載禁止"
    )

if __name__ == "__main__":
    print("flavor_5ch: stub（翻案専用・生レス転載禁止）")
