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
"""

COMMON_RULES = (
    "- 話者名は必ず次の6名のみを一字一句そのまま使う（改変・別名・誤字は禁止）：\n"
    "  四国めたん / ずんだもん / 玄野武宏 / 青山龍星 / 九州そら / 春日部つむぎ。\n"
    "  ※「春日部つむぎ」を七尾つむぎ等に変えない。\n"
    "- 数値は必ず上の fact 値を使い、直後に [要ファクトチェック] を付ける。\n"
    "- 「最高値更新か」が「いいえ」の場合、「最高値更新」と書かない（事実に反するため）。\n"
    "- 各掛け合いブロックは最低8〜12レス。薄く終わらせない。\n"
    "- [IMG:key] は下記『使えるいらすとや素材』の key だけを使う（存在しないkeyを創作しない）。\n"
    "  場面の感情・話題に合う素材をレス直前に積極的に置く。ただし1動画で使うのは20点以内。\n"
    "- 出力は台本本文（【話者名】…）のみ。前置き・後書き・説明文は書かない。\n"
)

def build_catalog(chdir: pathlib.Path) -> str:
    """台帳 irasutoya.json を『使えるいらすとや素材』一覧としてLLMへ渡す文字列に。"""
    m = json.loads((chdir / "assets" / "irasutoya.json").read_text(encoding="utf-8"))
    groups = {}
    for a in m["assets"]:
        groups.setdefault(a.get("group", "その他"), []).append(f"{a['key']}({a['desc']})")
    lines = ["## 使えるいらすとや素材（[IMG:key] はこのkeyだけ）"]
    for g, items in groups.items():
        lines.append(f"- {g}: " + " / ".join(items))
    return "\n".join(lines)

# 章分割マルチパス（17ブロックを3部に分割 → 各部opusで生成し結合 → 単発の頭打ちを回避し30分尺に到達）
PASSES = [
    ("第1部 掴み・対立", True,
     "ブロック1〜6（1導入/2問題提起/3逆張り登場/4定義/5解説①実質金利[GRAPH:]/6ドル指数）を書く。"
     "冒頭に # タイトル行（【2chゴールドスレ】＋フック＋【2ch有益スレ】）とナレーター導入を置き、価格はここで一度だけ提示する。"),
    ("第2部 種明かし", False,
     "ブロック7〜12（7有事/8インフレ/9中銀買い/10解説②長期チャート[GRAPH:]/11金vsBTC/12金vs米国株）を書く。"
     "# タイトルや導入は書かない。直前の会話の続きから自然に始め、同じ論点・レスを繰り返さない。"),
    ("第3部 実需オチ", False,
     "ブロック13〜17（13現物vsETFvs積立/14ワイの体験談で山場/15買い時と積立[GRAPH:]/16税金・出口/17結論+CTA）を書く。"
     "# タイトルや導入は書かない。必ずナレーターの結論と、コメント誘導・登録/高評価/スパチャのCTAで締める。"),
]

def _strip_leading_title(text: str) -> str:
    lines = text.splitlines()
    return "\n".join(l for l in lines if not l.strip().startswith("#")).strip()

def call_claude(system_and_prompt: str) -> str:
    key = os.environ["ANTHROPIC_API_KEY"]
    body = json.dumps({
        "model": MODEL, "max_tokens": int(os.environ.get("INGEST_MAX_TOKENS", "32000")),
        "messages": [{"role": "user", "content": system_and_prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"})
    timeout = int(os.environ.get("INGEST_HTTP_TIMEOUT", "600"))  # opusは長尺で>180sになる
    resp = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
    return "".join(b.get("text", "") for b in resp.get("content", []))

def main(channel: str, ep: str) -> int:
    root = pathlib.Path(__file__).resolve().parents[2]
    chdir = root / "channels" / channel
    ingest = json.loads((chdir / "ingest.json").read_text(encoding="utf-8"))
    prompt_spec = (chdir / "script_prompt.md").read_text(encoding="utf-8")
    ledger_path = chdir / "topic_ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() \
        else {"generated": []}

    params = build_params(ingest, ledger)
    base = prompt_spec + "\n\n" + params + "\n\n" + build_catalog(chdir)
    passes = int(os.environ.get("INGEST_PASSES", "3"))   # 既定3部マルチパス。1で単発

    if not os.environ.get("ANTHROPIC_API_KEY"):
        outp = chdir / "out" / f"{ep}.prompt.txt"
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(base + "\n\n## 指示\n③に従い全17ブロックを書く。\n" + COMMON_RULES, encoding="utf-8")
        print(f"[slot_fill] ANTHROPIC_API_KEY未設定 → 充填済みプロンプトを {outp} に出力（手貼り互換）。")
        return 0

    if passes >= 2:
        acc = []
        for i, (name, is_head, instr) in enumerate(PASSES):
            tail = "\n".join("\n".join(acc).splitlines()[-14:]) if acc else ""
            msg = base
            if tail:
                msg += "\n\n## ここまでの流れ（これに続けて書く。繰り返さない）\n" + tail
            msg += f"\n\n## 今回書く範囲：{name}\n{instr}\n{COMMON_RULES}"
            out = call_claude(msg)
            out = out.strip() if is_head else _strip_leading_title(out)
            acc.append(out)
            n = sum(len(l) for l in out.splitlines() if l.startswith("【"))
            print(f"[slot_fill] {name}: 生成 {n}字")
        script = "\n".join(acc)
    else:
        script = call_claude(base + "\n\n## 指示\n③に従い全17ブロックを書く。\n" + COMMON_RULES)

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
