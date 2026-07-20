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
    # 「精密な数値」だけ [要ファクトチェック] 欠落を検出（丸め数字4000・年号5000年・回数20年は誤検知なので除外）
    #   精密＝小数(4023.6) / 桁区切り(21,011) / 5桁以上(21011)。
    precise = re.compile(r"\d\.\d|\d{1,3}(?:,\d{3})+|\d{5,}")
    for l in body_lines:
        body = re.sub(r"【[^】]+】", "", l)
        if precise.search(body) and "[要ファクトチェック]" not in l and "[GRAPH:" not in l:
            fails.append(f"C: 精密数値に[要ファクトチェック]欠落: {body[:24]}")

    # D: 尺
    body_chars = sum(len(re.sub(r"【[^】]+】|\[[^\]]+\]", "", l)) for l in body_lines)
    minutes = body_chars / CHARS_PER_MIN
    if body_chars < MIN_CHARS:
        fails.append(f"D: 本文 {body_chars}字（{minutes:.1f}分）< 下限 {MIN_CHARS}字。増補が必要")
    elif body_chars > MAX_CHARS * 1.05:      # 上限は5%の余裕を許容
        fails.append(f"D: 本文 {body_chars}字（{minutes:.1f}分）> 上限 {MAX_CHARS}字。やや長い（任意で圧縮）")

    # E: コンプラNG語（否定文脈「〜ではない/ありません」は許容＝誤検知回避）
    NEG = ("ない", "なく", "ありませ", "じゃ", "ではな", "でなく", "ません")
    for ng in NG_PATTERNS:
        for m in re.finditer(re.escape(ng), text):
            seg = text[m.end():].split("。")[0][:60]     # 同一文の残り（複合否定「〜でも〜でもありません」に対応）
            if not any(neg in seg for neg in NEG):
                fails.append(f"E: 禁止表現「{ng}」を検出（否定文脈でない）")
                break

    return fails

def check_images(channel: str, text: str) -> list:
    """B: [IMG:key] が台帳に存在するか＋いらすとや使用点数(≤20)。"""
    import json as _json
    root = pathlib.Path(__file__).resolve().parents[2]
    man = root / "channels" / channel / "assets" / "irasutoya.json"
    keys = {a["key"] for a in _json.loads(man.read_text(encoding="utf-8"))["assets"]} if man.exists() else set()
    used = re.findall(r"\[IMG:\s*([\w-]+)\s*\]", text)
    fails = []
    for k in sorted(set(used)):
        if k not in keys:
            fails.append(f"B: 台帳に無い[IMG:{k}]（存在するkeyに直すか台帳へ登録）")
    if len(set(used)) > 20:
        fails.append(f"B: いらすとや使用 {len(set(used))}点 > 20（商用ルール。減らす）")
    return fails

def main(argv) -> int:
    channel = argv[0]
    text = load_script(channel, argv[1], argv[2:])
    fails = check(text) + check_images(channel, text)
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
