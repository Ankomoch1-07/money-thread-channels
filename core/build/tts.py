#!/usr/bin/env python3
"""台本(話者タグ付き .txt) を VOICEVOX で音声化。

  channels/<channel>/out/voice.wav      … 全結合音声
  channels/<channel>/out/subs.tsv       … 字幕(話者\tセリフ)
  channels/<channel>/out/timeline.json  … Remotion同期用タイムライン(フレーム単位, fps=30)
を出力する。[GRAPH:...] は直後の発話セグメントに graph 番号として紐づく。

channel_03/build/tts.py を <channel> 引数対応に一般化して移植。
usage: tts.py <channel> <script.txt>
"""
import sys, re, json, subprocess, requests, os, pathlib

ENG = "http://localhost:50021"
FPS = 30

def wav_seconds(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nokey=1:noprint_wrappers=1", path],
        capture_output=True, text=True).stdout.strip()
    return float(out) if out else 0.0

def main(channel: str, script_path: str) -> int:
    root = pathlib.Path(__file__).resolve().parents[2]
    chdir = root / "channels" / channel
    outdir = chdir / "out"
    (outdir / "wav").mkdir(parents=True, exist_ok=True)
    spk = json.load(open(chdir / "speakers.json", encoding="utf-8"))
    lines = open(script_path, encoding="utf-8").read().splitlines()

    parts, subs, segs = [], [], []
    pending_graph = None      # 次の発話に紐づけるグラフ番号
    pending_img = None        # 次の発話に紐づける いらすとや素材キー
    graph_count = 0
    title = ""
    i = 0

    for ln in lines:
        s = ln.strip()
        if s.startswith("#") and not title:                  # 動画タイトル→スレタイ帯へ
            title = re.sub(r"【.*?】", "", s.lstrip("# ")).strip()
            continue
        if s.startswith("[GRAPH"):
            pending_graph = graph_count
            graph_count += 1
            continue
        mi = re.match(r"\[IMG:\s*([\w-]+)\s*\]", s)           # いらすとや素材の明示指定
        if mi:
            pending_img = mi.group(1)
            continue
        m = re.match(r"【(.+?)】(.+)", ln)
        if not m:
            continue                                          # #タイトル等はスキップ
        name, txt = m.group(1), m.group(2)
        txt = re.sub(r"\[.*?\]", "", txt).strip()             # [要ファクトチェック]等を除去
        if not txt:
            continue
        sid = spk.get(name, 3)
        q = requests.post(f"{ENG}/audio_query", params={"text": txt, "speaker": sid}).json()
        q["speedScale"] = 1.05                                # ゆっくりめで好みで
        wav = requests.post(f"{ENG}/synthesis", params={"speaker": sid}, json=q).content
        p = outdir / "wav" / f"{i:04d}.wav"
        open(p, "wb").write(wav)
        parts.append(str(p))
        subs.append(f"{name}\t{txt}")
        segs.append({"i": i, "name": name, "text": txt,
                     "sec": None, "graph": pending_graph, "img": pending_img})
        pending_graph = None
        pending_img = None
        i += 1

    # 無音0.35秒パディングを挟んで結合しつつ、各セグメントのフレーム位置を確定
    PAD = 0.35
    listfile = outdir / "list.txt"
    with open(listfile, "w") as f:
        for p in parts:
            f.write(f"file '{os.path.abspath(p)}'\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
                    "-af", f"apad=pad_dur={PAD}", str(outdir / "voice.wav")])

    cur = 0
    for seg in segs:
        dur = wav_seconds(str(outdir / "wav" / f"{seg['i']:04d}.wav")) + PAD
        seg["start"] = round(cur * FPS)
        seg["dur"] = max(1, round(dur * FPS))
        del seg["sec"]
        cur += dur

    json.dump({"fps": FPS, "title": title, "segments": segs},
              open(outdir / "timeline.json", "w", encoding="utf-8"), ensure_ascii=False)
    open(outdir / "subs.tsv", "w", encoding="utf-8").write("\n".join(subs))
    print(f"done: {outdir}/voice.wav / timeline.json ({len(segs)} segs, {graph_count} graphs)")
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: tts.py <channel> <script.txt>"); sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
