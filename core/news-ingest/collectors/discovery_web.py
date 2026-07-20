#!/usr/bin/env python3
"""discovery層：WebSearchで突発ネタを補完（定常コレクターの拾い漏れ）。

sources.yaml の layers.discovery.web_queries を回し、スニペットを翻案して extra_topics に格納。
fact層のフォールバック（無料枠が尽きた/落ちた日の価格拾い）もここに寄せられる。
"""
from __future__ import annotations

def collect(web_queries: list[str]) -> dict:
    """{extra_topics: [...]} を返す（TODO: WebSearch接続）。"""
    raise NotImplementedError("WebSearchでクエリを回し、スニペット→翻案→extra_topics")

if __name__ == "__main__":
    print("discovery_web: stub")
