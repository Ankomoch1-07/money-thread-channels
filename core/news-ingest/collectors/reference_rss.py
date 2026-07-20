#!/usr/bin/env python3
"""reference層：ニュースRSSから金関連の見出し・要約・URLを収集。

RSS優先。本文はコピーしない（見出し/要約/URLのみ保持）。
金関連キーワードで絞り込み＋直近lookbackHours。why_moved(因果)は digest.py がLLMで論点化。
sources.yaml の layers.reference.rss / keywords を使う。
"""
from __future__ import annotations

def collect(rss_sources: list[dict], keywords: list[str], lookback_hours: int) -> list[dict]:
    """[{title, url, publisher, published, summary}] を返す（TODO: feedparser実装）。"""
    raise NotImplementedError("feedparser でRSS取得→キーワード＆時刻フィルタ→正規化")

if __name__ == "__main__":
    print("reference_rss: stub")
