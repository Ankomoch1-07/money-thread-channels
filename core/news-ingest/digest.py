#!/usr/bin/env python3
"""ダイジェスト化：referenceの見出し群をLLMで論点化し topic / why_moved を作る。

factの数値には触らない（数値はfact層そのまま）。ここは「なぜ動いたか」を
実質金利/ドル/有事/インフレ/中銀買い の枠で1〜2文に整理するだけ。
"""
from __future__ import annotations

def digest(reference_items: list[dict]) -> dict:
    """{topic, why_moved, sources} を返す（TODO: LLM呼び出し）。"""
    raise NotImplementedError("referenceの見出し→LLMで topic/why_moved を論点化")

if __name__ == "__main__":
    print("digest: stub")
