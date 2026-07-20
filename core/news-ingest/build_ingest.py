#!/usr/bin/env python3
"""4層を束ねて ingest.json を出力（news-ingest ⇄ core の契約）。

usage: build_ingest.py <channel>

channels/<channel>/sources.yaml を読み、各collectorを実行して
channels/<channel>/ingest.json（NEWS_INGEST.md のスキーマ）を書き出す。

可用性ルール：
- fact層のみ required。取得できなければ中断（数値が無いと台本が書けない）。
- reference/flavor/discovery は best-effort。失敗/未設定はスキップし、欠けたことをログに残す。
"""
import sys, json, pathlib, datetime
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import yaml
from collectors import fact_price, reference_rss, flavor_5ch, discovery_web
import rank, digest

def log(msg): print(f"[ingest] {msg}")

def main(channel: str) -> int:
    root = pathlib.Path(__file__).resolve().parents[2]
    chdir = root / "channels" / channel
    cfg = yaml.safe_load((chdir / "sources.yaml").read_text(encoding="utf-8"))
    layers = cfg.get("layers", {})
    lookback = cfg.get("lookbackHours", 24)
    kw = layers.get("reference", {}).get("keywords", [])

    # fact（必須）
    try:
        fact = fact_price.fetch()
        log(f"fact OK: XAU/USD={fact['xau_usd']} 円/g={fact['jpy_per_gram']} "
            f"最高値圏={fact['is_record_high']}")
    except Exception as e:
        log(f"fact FAILED（必須）: {e!r} → 中断"); return 1

    # reference（best-effort）
    reference = {"topic": "", "why_moved": "", "sources": []}
    try:
        items = reference_rss.collect(layers.get("reference", {}).get("rss", []), kw, lookback)
        reference = digest.digest(rank.rank(items, kw, top_n=5))
        log(f"reference OK: {len(reference['sources'])}件 → why_moved='{reference['why_moved']}'"
            if reference["sources"] else "reference: 該当なし（スキップ）")
    except Exception as e:
        log(f"reference skip: {e!r}")

    # flavor（best-effort・翻案専用）
    flavor = {}
    if layers.get("flavor", {}).get("enabled"):
        try:
            flavor = flavor_5ch.collect(layers["flavor"].get("sources", []), kw)
            log(f"flavor OK: mood='{flavor.get('mood')}'" if flavor else "flavor: 取得なし（スキップ）")
        except Exception as e:
            log(f"flavor skip: {e!r}")

    # discovery（best-effort）
    discovery = {}
    try:
        discovery = discovery_web.collect(layers.get("discovery", {}).get("web_queries", []))
        log(f"discovery OK: {len(discovery.get('extra_topics', []))}件"
            if discovery else "discovery: スキップ（検索APIキー未設定）")
    except Exception as e:
        log(f"discovery skip: {e!r}")

    ingest = {
        "date": datetime.datetime.now(datetime.timezone.utc).date().isoformat(),
        "fact": fact, "reference": reference, "flavor": flavor, "discovery": discovery,
    }
    out = chdir / "ingest.json"
    out.write_text(json.dumps(ingest, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"→ {out}")
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: build_ingest.py <channel>"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
