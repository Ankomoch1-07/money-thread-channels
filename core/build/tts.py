#!/usr/bin/env python3
"""台本(話者タグ付き .txt) を VOICEVOX で音声化し、channels/<channel>/out/ に
  voice.wav / subs.tsv / timeline.json を出力する。
channel_03(fx-2ch)の tts.py を monorepo用に <channel> 引数対応へ移植。
- phase: [OP_HOOK]/[OP_TITLE]/[OP_DESC]/[ED] を次の発話へ付与、その後 main へ戻る。
- [OPIMG:] / [EDIMG:] : OP/EDカード用画像リスト。[BG:]/[OPBG:] : 背景の明示指定(任意)。
- [GRAPH:...] は直後の発話へ、[IMG:key] は以降ずっと継続(sticky)。
- desc/ed の発話は telop(チャンク分割)を付与。
- 音声結合・尺計算は標準ライブラリ wave のみ(ffmpeg不要)。背景は public/<ch>/bg を本編/OPで別々にローテ。
usage: tts.py <channel> <script.txt>
"""
import sys, re, json, wave, requests, os, glob, pathlib, struct

ENG = "http://localhost:50021"
FPS = 30
PAD = 0.35
SPEED = {
    "四国めたん": 1.01, "ずんだもん": 1.17, "玄野武宏": 0.95,
    "青山龍星": 1.02, "九州そら": 1.53, "春日部つむぎ": 1.05, "No.7": 1.00,
}

def _atom_seconds(data, tag):
    i = data.find(tag)
    if i < 0:
        return None
    ver = data[i + 4]
    try:
        if ver == 0:
            ts = struct.unpack(">I", data[i + 16:i + 20])[0]
            dur = struct.unpack(">I", data[i + 20:i + 24])[0]
        else:
            ts = struct.unpack(">I", data[i + 24:i + 28])[0]
            dur = struct.unpack(">Q", data[i + 28:i + 36])[0]
        return (dur / ts) if (ts and dur) else None
    except struct.error:
        return None

def mp4_duration(path):
    try:
        data = open(path, "rb").read()
    except OSError:
        return None
    return _atom_seconds(data, b"mvhd") or _atom_seconds(data, b"mdhd")

def chunk_telop(text, size=22, hardmax=40):
    parts = re.split(r"(?<=[。、！？])", text)
    chunks, buf = [], ""
    for p in parts:
        if not p:
            continue
        if len(buf) + len(p) <= size:
            buf += p; continue
        if buf:
            chunks.append(buf); buf = ""
        if len(p) <= hardmax:
            buf = p
        else:
            for j in range(0, len(p), size):
                chunks.append(p[j:j + size])
    if buf:
        chunks.append(buf)
    return chunks

def main(channel, script_path):
    root = pathlib.Path(__file__).resolve().parents[2]
    chdir = root / "channels" / channel
    outdir = chdir / "out"
    (outdir / "wav").mkdir(parents=True, exist_ok=True)
    pub = root / "core" / "remotion" / "public" / channel
    spk = json.load(open(chdir / "speakers.json", encoding="utf-8"))
    lines = open(script_path, encoding="utf-8").read().splitlines()
    ep = os.path.splitext(os.path.basename(script_path))[0]

    parts, subs, segs = [], [], []
    pending_graph = None
    current_img = None
    pending_phase = "main"
    op_images, ed_images = [], []
    forced_bg = forced_opbg = None
    graph_count = 0
    title = ""
    i = 0

    for ln in lines:
        s = ln.strip()
        if s.startswith("#") and not title:
            title = re.sub(r"【.*?】", "", s.lstrip("# ")).strip(); continue
        if s == "[OP_HOOK]":  pending_phase = "hook"; continue
        if s == "[OP_TITLE]": pending_phase = "title"; continue
        if s == "[OP_DESC]":  pending_phase = "desc"; continue
        if s == "[ED]":       pending_phase = "ed"; continue
        mo = re.match(r"\[OPIMG:\s*(.+?)\]", s)
        if mo: op_images = [x.strip() for x in mo.group(1).split(",") if x.strip()]; continue
        me = re.match(r"\[EDIMG:\s*(.+?)\]", s)
        if me: ed_images = [x.strip() for x in me.group(1).split(",") if x.strip()]; continue
        mb = re.match(r"\[BG:\s*(.+?)\]", s)
        if mb: forced_bg = mb.group(1).strip(); continue
        mob = re.match(r"\[OPBG:\s*(.+?)\]", s)
        if mob: forced_opbg = mob.group(1).strip(); continue
        if s.startswith("[GRAPH"):
            pending_graph = graph_count; graph_count += 1; continue
        mi = re.match(r"\[IMG:\s*([\w-]+)\s*\]", s)
        if mi: current_img = mi.group(1); continue
        m = re.match(r"【(.+?)】(.+)", ln)
        if not m:
            continue
        name, txt = m.group(1), re.sub(r"\[.*?\]", "", m.group(2)).strip()
        if not txt:
            continue
        speak = re.sub(r"[wWｗＷ]+", "", txt).strip() or txt   # 草のwは字幕に残すが読み上げない
        sid = spk.get(name, 3)
        q = requests.post(f"{ENG}/audio_query", params={"text": speak, "speaker": sid}).json()
        q["speedScale"] = SPEED.get(name, 1.05)
        wav_bytes = requests.post(f"{ENG}/synthesis", params={"speaker": sid}, json=q).content
        p = outdir / "wav" / f"{i:04d}.wav"
        open(p, "wb").write(wav_bytes)
        parts.append(str(p)); subs.append(f"{name}\t{txt}")
        seg = {"i": i, "name": name, "text": txt,
               "graph": pending_graph, "img": current_img, "phase": pending_phase}
        if pending_phase in ("desc", "ed"):
            seg["telop"] = chunk_telop(txt)
        segs.append(seg)
        pending_graph = None; pending_phase = "main"; i += 1

    params = None; durations = []; frames = []
    for p in parts:
        w = wave.open(p, "rb")
        if params is None: params = w.getparams()
        durations.append(w.getnframes() / w.getframerate() + PAD)
        frames.append(w.readframes(w.getnframes())); w.close()
    silence = b"\x00" * (int(params.framerate * PAD) * params.sampwidth * params.nchannels)
    out = wave.open(str(outdir / "voice.wav"), "wb"); out.setparams(params)
    for fr in frames:
        out.writeframes(fr); out.writeframes(silence)
    out.close()

    cur = 0.0
    for seg, dur in zip(segs, durations):
        seg["start"] = round(cur * FPS); seg["dur"] = max(1, round(dur * FPS)); cur += dur

    se_files = glob.glob(str(pub / "se" / "*.mp3")) + glob.glob(str(pub / "se" / "*.wav"))
    se_path = ("se/" + os.path.basename(se_files[0])) if se_files else None

    # 背景：public/<ch>/bg の mp4/mov をエピソードごとに本編/OPで別々にローテ。重い(>30MB)は自動除外。
    MAXBG = 30 * 1024 * 1024
    _bg_all = sorted(glob.glob(str(pub / "bg" / "*.mp4")) + glob.glob(str(pub / "bg" / "*.mov")))
    bg_pool = [os.path.basename(p) for p in _bg_all if os.path.getsize(p) <= MAXBG]
    _heavy = [os.path.basename(p) for p in _bg_all if os.path.getsize(p) > MAXBG]
    _num = re.search(r"\d+", ep)
    _idx = int(_num.group()) if _num else abs(hash(ep)) % 997
    def pick_bg(offset, forced, fallback):
        if forced:
            f = forced if forced.startswith("bg/") else "bg/" + forced
            if os.path.basename(f) in bg_pool and (pub / f).exists():
                return f
        if bg_pool:
            return "bg/" + bg_pool[(_idx + offset) % len(bg_pool)]
        return fallback
    main_bg = pick_bg(0, forced_bg, "bg/gold.png")
    op_bg = pick_bg(1, forced_opbg, "bg/gold.png")
    def bg_frames(bg):
        d = mp4_duration(str(pub / bg))
        return max(1, int(d * FPS) - 1) if d else 240
    main_bg_frames = bg_frames(main_bg); op_bg_frames = bg_frames(op_bg)
    print(f"bg: 本編={main_bg}({main_bg_frames}f) / OP={op_bg}({op_bg_frames}f) （ローテ対象{len(bg_pool)}本" +
          (f" ／ 重すぎ除外: {_heavy}" if _heavy else "") + "）")

    # BGM：public/<ch>/bgm/ の音源をエピソードごとにローテ。Board側でループ＋小音量で全編に敷く。
    bgm_all = sorted(glob.glob(str(pub / "bgm" / "*.mp3")) + glob.glob(str(pub / "bgm" / "*.wav")))
    bgm_path = ("bgm/" + os.path.basename(bgm_all[_idx % len(bgm_all)])) if bgm_all else None
    print(f"bgm: {bgm_path or '（なし）'}（候補{len(bgm_all)}本）")

    json.dump({"fps": FPS, "title": title, "opImages": op_images, "edImages": ed_images,
               "se": se_path, "bgm": bgm_path, "bg": main_bg, "opBg": op_bg,
               "bgFrames": main_bg_frames, "opBgFrames": op_bg_frames, "segments": segs},
              open(outdir / "timeline.json", "w", encoding="utf-8"), ensure_ascii=False)
    open(outdir / "subs.tsv", "w", encoding="utf-8").write("\n".join(subs))
    total = cur
    print(f"done: {outdir}/voice.wav ({total:.0f}s/{total/60:.1f}分) / timeline.json ({len(segs)} segs, {graph_count} graphs)")
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: tts.py <channel> <script.txt>"); sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
