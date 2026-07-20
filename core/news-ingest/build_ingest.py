#!/usr/bin/env python3
"""4層を束ねて ingest.json を出力（news-ingest ⇄ core の契約）。

usage: build_ingest.py <channel>

channels/<channel>/sources.yaml を読み、各collectorを実行して
channels/<channel>/ingest.json（NEWS_INGEST.md のスキーマ）を書き出す。

可用性ルール：
- fact層のみ required=True。取得できなければ中断（数値が無いと台本が書けない）。
- reference/flavor/discovery は best-effort。失敗した層はスキップし、欠けたことをログに残す（silent fail禁止）。
"""
import sys, json, pathlib

def main(channel: str) -> int:
    root = pathlib.Path(__file__).resolve().parents[2]
    chdir = root / "channels" / channel
    # sources = yaml.safe_load((chdir / "sources.yaml").read_text())  # TODO
    #
    # fact = fact_price.fetch(...)                      # required
    # reference = digest.digest(rank.rank(reference_rss.collect(...)))   # best-effort
    # flavor = flavor_5ch.collect(...)                  # best-effort（翻案専用）
    # discovery = discovery_web.collect(...)            # best-effort
    # ingest = {date, fact, reference, flavor, discovery}
    # (chdir / "ingest.json").write_text(json.dumps(ingest, ensure_ascii=False, indent=2))
    raise NotImplementedError("collectors→rank→digest を束ねて ingest.json を出力")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: build_ingest.py <channel>"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
