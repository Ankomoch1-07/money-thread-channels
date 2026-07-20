#!/usr/bin/env python3
"""ffmpeg/VOICEVOX無しで、台本から timeline.json を「推定尺」で生成する開発/プレビュー用ヘルパ。

本番の tts.py は実音声の長さで dur を決めるが、こちらは文字数から尺を推定するだけ。
Remotionの映像プレビュー/静止画レンダ(実素材・レイアウト確認)を、音声パイプライン抜きで回すために使う。
出力先は core/remotion/public/<channel>/<ep>/timeline.json（run.shの配置先と同じ）。

usage: timeline_from_script.py <channel> <ep> <script.txt>
"""
import sys, re, json, pathlib

FPS = 30
CHARS_PER_SEC = 7.0     # おおよその読み上げ速度（推定）
MIN_FRAMES = 24

def main(channel: str, ep: str, script_path: str) -> int:
    root = pathlib.Path(__file__).resolve().parents[2]
    lines = open(script_path, encoding="utf-8").read().splitlines()
    segs, title = [], ""
    pending_graph, pending_img, graph_count, i, cur = None, None, 0, 0, 0

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
        dur = max(MIN_FRAMES, round(len(txt) / CHARS_PER_SEC * FPS))
        segs.append({"i": i, "name": name, "text": txt, "start": cur, "dur": dur,
                     "graph": pending_graph, "img": pending_img})
        cur += dur; pending_graph = None; pending_img = None; i += 1

    dest = root / "core" / "remotion" / "public" / channel / ep
    dest.mkdir(parents=True, exist_ok=True)
    json.dump({"fps": FPS, "title": title, "segments": segs},
              open(dest / "timeline.json", "w", encoding="utf-8"), ensure_ascii=False)
    print(f"timeline.json ({len(segs)} segs, {cur} frames ≈ {cur/FPS/60:.1f}分) -> {dest}")
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("usage: timeline_from_script.py <channel> <ep> <script.txt>"); sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
