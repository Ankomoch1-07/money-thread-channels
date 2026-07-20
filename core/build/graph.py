#!/usr/bin/env python3
"""台本の [GRAPH: タイトル | ラベル:値, ラベル:値, ... | Y軸ラベル] を解析し棒グラフPNGを
channels/<channel>/out/graph/NN.png に出力。データ無しの [GRAPH: 説明] はフォールバック簡易表示。
channel_03(fx-2ch)版を <channel> 引数対応へ移植。
usage: graph.py <channel> <script.txt>
"""
import re, sys, os, pathlib
import matplotlib
matplotlib.use("Agg")
try:
    import japanize_matplotlib  # noqa: F401
except Exception:
    matplotlib.rcParams["font.family"] = [
        "Noto Sans CJK JP", "IPAexGothic", "Hiragino Sans", "TakaoPGothic", "sans-serif"]
import matplotlib.pyplot as plt

def parse(cue):
    body = re.sub(r"^\[GRAPH:?", "", cue).strip().rstrip("]").strip()
    parts = [p.strip() for p in body.split("|")]
    title = parts[0] if parts else ""
    labels, values = [], []
    if len(parts) >= 2:
        for pair in parts[1].split(","):
            if ":" in pair:
                k, v = pair.rsplit(":", 1)
                labels.append(k.strip())
                try:
                    values.append(float(re.sub(r"[^0-9.\-]", "", v)))
                except ValueError:
                    values.append(0.0)
    ylabel = parts[2] if len(parts) >= 3 else ""
    return title, labels, values, ylabel

def main(channel, script_path):
    root = pathlib.Path(__file__).resolve().parents[2]
    gdir = root / "channels" / channel / "out" / "graph"
    gdir.mkdir(parents=True, exist_ok=True)
    cues = [l.strip() for l in open(script_path, encoding="utf-8") if l.strip().startswith("[GRAPH")]
    for idx, c in enumerate(cues):
        title, labels, values, ylabel = parse(c)
        if not labels:
            labels, values, ylabel = ["データA", "データB"], [50, 50], ""
        fig, ax = plt.subplots(figsize=(16, 9), dpi=120)
        colors = ["#2e7d32"] + ["#c62828"] * (len(labels) - 1)
        ax.bar(labels, values, color=colors[:len(labels)])
        ax.set_title(title, fontsize=30, pad=20)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=22)
        top = max(values) if values else 100
        ax.set_ylim(0, top * 1.25)
        for i, v in enumerate(values):
            ax.text(i, v + top * 0.02, f"{v:g}", ha="center", fontsize=28, fontweight="bold")
        ax.tick_params(labelsize=22)
        fig.savefig(gdir / f"{idx:02d}.png", bbox_inches="tight")
        plt.close(fig)
    print(f"{len(cues)} graphs -> {gdir}/")
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: graph.py <channel> <script.txt>"); sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
