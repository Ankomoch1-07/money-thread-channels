#!/usr/bin/env python3
"""台本(話者タグ付き .txt) を VOICEVOX で音声化。

  channels/<channel>/out/voice.wav      … 全結合音声
  channels/<channel>/out/subs.tsv       … 字幕(話者\tセリフ)
  channels/<channel>/out/timeline.json  … Remotion同期用タイムライン(フレーム単位, fps=30)
を出力する。[GRAPH:...] は直後の発話セグメントに graph 番号として紐づく。

channel_03/build/tts.py を移植し、ffmpeg/ffprobe依存を撤去（標準ライブラリ wave で結合・尺算出）。
usage: tts.py <channel> <script.txt>
"""
import sys, re, json, os, pathlib, wave, struct, requests

ENG = "http://localhost:50021"
FPS = 30
PAD = 0.35   # 各発話間の無音パディング秒

def main(channel: str, script_path: str) -> int:
    root = pathlib.Path(__file__).resolve().parents[2]
    chdir = root / "channels" / channel
    outdir = chdir / "out"
    (outdir / "wav").mkdir(parents=True, exist_ok=True)
    spk = json.load(open(chdir / "speakers.json", encoding="utf-8"))
    lines = open(script_path, encoding="utf-8").read().splitlines()

    segs, subs, wav_paths = [], [], []
    pending_graph = pending_img = None
    graph_count = 0
    title = ""
    i = 0

    for ln in lines:
        s = ln.strip()
        if s.startswith("#") and not title:
            title = re.sub(r"【.*?】", "", s.lstrip("# ")).strip(); continue
        if s.startswith("[GRAPH"):
            pending_graph = graph_count; graph_count += 1; continue
        mi = re.match(r"\[IMG:\s*([\w-]+)\s*\]", s)
        if mi:
            pending_img = mi.group(1); continue
        m = re.match(r"【(.+?)】(.+)", ln)
        if not m:
            continue
        name, txt = m.group(1), re.sub(r"\[.*?\]", "", m.group(2)).strip()
        if not txt:
            continue
        sid = spk.get(name, 3)
        q = requests.post(f"{ENG}/audio_query", params={"text": txt, "speaker": sid}).json()
        q["speedScale"] = 1.05
        wav = requests.post(f"{ENG}/synthesis", params={"speaker": sid}, json=q).content
        p = outdir / "wav" / f"{i:04d}.wav"
        open(p, "wb").write(wav)
        wav_paths.append(p)
        subs.append(f"{name}\t{txt}")
        segs.append({"i": i, "name": name, "text": txt,
                     "graph": pending_graph, "img": pending_img})
        pending_graph = pending_img = None
        i += 1

    if not wav_paths:
        print("no speech lines found"); return 1

    # wave で結合（PAD秒の無音を挟む）しつつ、各セグメントのフレーム位置を確定
    with wave.open(str(wav_paths[0]), "rb") as w0:
        nch, sw, fr = w0.getnchannels(), w0.getsampwidth(), w0.getframerate()
    silence = b"\x00" * int(fr * PAD) * sw * nch

    out_wav = wave.open(str(outdir / "voice.wav"), "wb")
    out_wav.setnchannels(nch); out_wav.setsampwidth(sw); out_wav.setframerate(fr)
    cur_frames = 0
    for seg, p in zip(segs, wav_paths):
        with wave.open(str(p), "rb") as w:
            frames = w.readframes(w.getnframes())
            dur_frames_audio = w.getnframes()
        out_wav.writeframes(frames)
        out_wav.writeframes(silence)
        total = dur_frames_audio + int(fr * PAD)
        seg["start"] = round(cur_frames / fr * FPS)
        seg["dur"] = max(1, round(total / fr * FPS))
        cur_frames += total
    out_wav.close()

    json.dump({"fps": FPS, "title": title, "segments": segs},
              open(outdir / "timeline.json", "w", encoding="utf-8"), ensure_ascii=False)
    open(outdir / "subs.tsv", "w", encoding="utf-8").write("\n".join(subs))
    total_sec = cur_frames / fr
    print(f"done: {outdir}/voice.wav ({total_sec:.1f}s / {total_sec/60:.1f}分), "
          f"timeline.json ({len(segs)} segs, {graph_count} graphs)")
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: tts.py <channel> <script.txt>"); sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
