#!/usr/bin/env python3
"""ダイジェスト化：referenceの見出し群から topic / why_moved を作る。

現状はLLM無しのヒューリスティック（マクロ用語→日本語の因果へマップ）。
本番では digest_llm() に差し替え、見出し群をLLMで1〜2文に論点化する（TODO）。
factの数値には触らない（数値はfact層そのまま）。
"""
from __future__ import annotations

# マクロ用語（英/日）→ 種明かしパートの因果表現
MACRO_MAP = {
    "real rate": "実質金利の動き", "real yield": "実質金利の動き", "yield": "金利の動き",
    "rate cut": "利下げ観測", "rate": "金利観測", "fed": "FRBの金融政策観測",
    "dollar": "ドルの動き", "inflation": "インフレ動向",
    "safe-haven": "有事の逃避需要", "safe haven": "有事の逃避需要",
    "geopolit": "地政学リスク", "war": "地政学リスク", "tension": "地政学リスク",
    "central bank": "中央銀行の金買い", "record": "最高値圏の話題",
    "実質金利": "実質金利の動き", "利下げ": "利下げ観測", "中央銀行": "中央銀行の金買い",
}

def digest(reference_items: list[dict]) -> dict:
    """{topic, why_moved, sources} を返す。"""
    if not reference_items:
        return {"topic": "", "why_moved": "", "sources": []}
    top = reference_items[0]
    blob = " ".join((it.get("title") or "") for it in reference_items).lower()
    causes = []
    for term, jp in MACRO_MAP.items():
        if term in blob and jp not in causes:
            causes.append(jp)
    why_moved = "＋".join(causes[:3]) if causes else "（マクロ要因は要確認）"
    return {
        "topic": top.get("title", ""),
        "why_moved": why_moved,
        "sources": [{"title": it.get("title"), "url": it.get("url"),
                     "publisher": it.get("publisher")} for it in reference_items[:5]],
        "_note": "why_movedはヒューリスティック抽出。LLM digestに差し替え予定",
    }

if __name__ == "__main__":
    print("digest: import OK")
