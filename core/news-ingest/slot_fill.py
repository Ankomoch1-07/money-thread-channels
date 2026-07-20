#!/usr/bin/env python3
"""ingest.json → script_prompt の {{ }} を埋めてLLM③台本生成を実行。

usage: slot_fill.py <channel> <ep>

- channels/<channel>/ingest.json と script_prompt.md を読む
- NEWS_INGEST.md のマッピングに従い {{ }} を充填
    fact.*        → 「今回の相場ファクト」([要ファクトチェック]付き) ＆ ⑤QAの fact層データ
    reference.topic    → 「今の相場ネタ」「スレタイ/テーマ」の種
    reference.why_moved→ 「なぜ動いたか」
    flavor.mood        → 作風の温度感
    discovery.*        → ①ネタ生成の補助・別回ストック
- topic_ledger.json の既出スレタイ/軸を「除外リスト」として①へ渡す（日次のネタ被り防止）
- LLM③を実行 → channels/<channel>/scripts/<ep>.txt を出力
- 採用スレタイ/軸を topic_ledger.json に追記
"""
import sys

def main(channel: str, ep: str) -> int:
    raise NotImplementedError("ingest.json充填→topic_ledger除外→LLM③→scripts/<ep>.txt→ledger追記")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: slot_fill.py <channel> <ep>"); sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
