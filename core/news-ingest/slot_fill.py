#!/usr/bin/env python3
"""ingest.json → script_prompt を充填して ③台本生成を実行し scripts/<ep>.txt を出力。

- ingest.json（fact/reference/flavor）と script_prompt.md と topic_ledger.json を読む
- 「今回の生成パラメータ」ブロックを組み、script_prompt全文に連結（{{ }}の脆い置換はせず、
  仕様書＋当日の素材をLLMに渡す方式）
- topic_ledger の既出スレタイ/軸を「除外リスト」として渡す（日次のネタ被り防止）
- ANTHROPIC_API_KEY があれば Claude を呼んで台本DSLを生成 → scripts/<ep>.txt、
  無ければ充填済みプロンプトを out/<ep>.prompt.txt に書き出し（channel_03の手貼り運用に橋渡し）
- 生成できたら topic を topic_ledger に追記

usage: slot_fill.py <channel> <ep>
"""
import sys, os, json, pathlib, urllib.request, datetime

MODEL = os.environ.get("INGEST_MODEL", "claude-sonnet-5")

def build_params(ingest: dict, ledger: dict) -> str:
    f = ingest.get("fact", {})
    r = ingest.get("reference", {})
    fl = ingest.get("flavor", {})
    rec = "はい（最高値圏）" if f.get("is_record_high") else \
        f"いいえ（現値 {f.get('xau_usd')} < 過去最高 {f.get('all_time_high_usd')} ドル）"
    seen = "／".join(g.get("topic", "") for g in ledger.get("generated", [])[-30:]) or "（なし）"
    src = "\n".join(f"    - {s.get('title')}" for s in r.get("sources", [])[:5])
    return f"""---
# 今回の生成（③ 台本生成プロンプトを実行）

## 素材（ingest.json・数値はこの fact 値のみを使うこと）
- 金価格: {f.get('xau_usd')} ドル/オンス（約 {f.get('jpy_per_gram')} 円/g）, 前日比 {f.get('change_pct_1d')}%
- 最高値更新か: {rec}
- 今の相場ネタ(topic): {r.get('topic')}
- なぜ動いたか(why_moved): {r.get('why_moved')}
- 参考見出し（翻案の参考。そのまま読み上げない）:
{src}
- スレのノリ(flavor): {fl.get('mood') or '—'}

## 除外（過去に扱った軸/スレタイ。被らせないこと）
{seen}

## 指示
script_prompt.md の「③ 台本生成プロンプト」に厳密に従い、上の素材で台本DSLを出力せよ。
- 数値は必ず上の fact 値を使い、直後に [要ファクトチェック] を付ける。
- 「最高値更新か」が「いいえ」の場合、「最高値更新」と書かない（事実に反するため）。
- 出力は台本本文（# タイトル行＋【話者名】…）のみ。前置き・後書きは不要。
"""

def call_claude(system_and_prompt: str) -> str:
    key = os.environ["ANTHROPIC_API_KEY"]
    body = json.dumps({
        "model": MODEL, "max_tokens": 16000,
        "messages": [{"role": "user", "content": system_and_prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"})
    resp = json.loads(urllib.request.urlopen(req, timeout=180).read())
    return "".join(b.get("text", "") for b in resp.get("content", []))

def main(channel: str, ep: str) -> int:
    root = pathlib.Path(__file__).resolve().parents[2]
    chdir = root / "channels" / channel
    ingest = json.loads((chdir / "ingest.json").read_text(encoding="utf-8"))
    prompt_spec = (chdir / "script_prompt.md").read_text(encoding="utf-8")
    ledger_path = chdir / "topic_ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))

    full = prompt_spec + "\n\n" + build_params(ingest, ledger)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        outp = chdir / "out" / f"{ep}.prompt.txt"
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(full, encoding="utf-8")
        print(f"[slot_fill] ANTHROPIC_API_KEY未設定 → 充填済みプロンプトを {outp} に出力。")
        print("            これをLLMに貼れば台本が得られます（channel_03の手貼り運用互換）。")
        return 0

    script = call_claude(full)
    sp = chdir / "scripts" / f"{ep}.txt"
    sp.parent.mkdir(parents=True, exist_ok=True)
    sp.write_text(script, encoding="utf-8")
    # topic_ledger 追記（被り防止）
    topic = ingest.get("reference", {}).get("topic", "") or ep
    ledger.setdefault("generated", []).append(
        {"date": ingest.get("date"), "ep": ep, "topic": topic})
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[slot_fill] 生成 → {sp}（ledgerに追記）")
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: slot_fill.py <channel> <ep>"); sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
