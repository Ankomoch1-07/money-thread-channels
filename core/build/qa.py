#!/usr/bin/env python3
"""自動QA（台本txtを機械チェック）。QA.md の項目 A–F。

usage: qa.py <channel> <ep>
       qa.py <channel> --script <path>

LLM内容QA(⑤)の前段。音声化する前に弾いて手戻りを最小化する。
A:DSL構文 / C:タグ数 / D:尺 / E:コンプラNG語 を実装。
B:素材整合 は check_assets.py に委譲、F:ファクト照合 は ingest.json 必須（未整備時はskip+警告）。
"""
import sys, re, json, pathlib

SPEAKERS = {"四国めたん", "ずんだもん", "玄野武宏", "青山龍星", "九州そら", "春日部つむぎ"}
NG_PATTERNS = ["必ず上がる", "必ず儲か", "絶対安全", "今すぐ買え", "絶対に儲か"]
CHARS_PER_MIN = 380          # 暫定。channel_03の実レンダで実測して確定する（QA.md 参照）
MIN_CHARS, MAX_CHARS = 10500, 12000

def load_script(channel: str, ep_or_flag: str, rest) -> str:
    root = pathlib.Path(__file__).resolve().parents[2]
    if ep_or_flag == "--script":
        return pathlib.Path(rest[0]).read_text(encoding="utf-8")
    return (root / "channels" / channel / "scripts" / f"{ep_or_flag}.txt").read_text(encoding="utf-8")

def check(text: str) -> list:
    fails = []
    lines = [l for l in text.splitlines() if l.strip()]
    body_lines = [l for l in lines if l.startswith("【")]

    # A: DSL構文
    if not lines or not lines[0].startswith("# "):
        fails.append("A: 冒頭の # タイトル行が無い")
    for l in body_lines:
        m = re.match(r"^【([^】]+)】", l)
        if not m:
            fails.append(f"A: 話者タグ不正: {l[:20]}")
        elif m.group(1) not in SPEAKERS:
            fails.append(f"A: 未定義の話者: {m.group(1)}")

    # C: タグ数
    n_graph = len(re.findall(r"\[GRAPH:", text))
    n_short = len(re.findall(r"\[SHORT候補\]", text))
    if n_graph < 2: fails.append(f"C: [GRAPH:] が {n_graph}（≥2 必要）")
    if n_short < 3: fails.append(f"C: [SHORT候補] が {n_short}（≥3 必要）")
    # 数値を含むが [要ファクトチェック] の無い本文行を検出
    for l in body_lines:
        body = re.sub(r"【[^】]+】", "", l)
        if re.search(r"[0-9０-９]", body) and "[要ファクトチェック]" not in l and "[GRAPH:" not in l:
            # 年号や番号だけの誤検知は許容度を上げる余地あり（TODO: 数値種別の判定）
            fails.append(f"C: 数値に[要ファクトチェック]欠落の可能性: {body[:24]}")

    # D: 尺
    body_chars = sum(len(re.sub(r"【[^】]+】|\[[^\]]+\]", "", l)) for l in body_lines)
    minutes = body_chars / CHARS_PER_MIN
    if body_chars < MIN_CHARS:
        fails.append(f"D: 本文 {body_chars}字（{minutes:.1f}分）< 下限 {MIN_CHARS}字。増補が必要")

    # E: コンプラNG語
    for ng in NG_PATTERNS:
        if ng in text:
            fails.append(f"E: 禁止表現「{ng}」を検出")

    return fails

def main(argv) -> int:
    channel = argv[0]
    text = load_script(channel, argv[1], argv[2:])
    fails = check(text)
    if fails:
        print("QA: 要修正")
        for f in fails: print("  -", f)
        return 1
    print("QA: 自動チェック合格（B素材整合とFファクト照合は別途）")
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: qa.py <channel> <ep> | qa.py <channel> --script <path>"); sys.exit(2)
    sys.exit(main(sys.argv[1:]))
