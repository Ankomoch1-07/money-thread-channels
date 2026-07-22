#!/usr/bin/env python3
"""台本の [GRAPH: タイトル | ラベル:値, ラベル:値, ... | Y軸ラベル] を解析し棒グラフPNGを
channels/<channel>/out/graph/NN.png に出力。データ無しの [GRAPH: 説明] はフォールバック簡易表示。
channel_03(fx-2ch)版を <channel> 引数対応へ移植。
usage: graph.py <channel> <script.txt>
"""
import re, sys, os, pathlib, logging
import matplotlib
from matplotlib import font_manager
matplotlib.use("Agg")
# 見つからないフォントの findfont 警告でログが埋まるのを抑止（CIはNoto CJKを使う）
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
try:
    import japanize_matplotlib  # noqa: F401  ローカルMac等
except Exception:
    # CI等：インストール済みの日本語フォントだけ指定（存在しない候補を並べると警告が大量に出る）
    for _f in ("Noto Sans CJK JP", "IPAexGothic", "Hiragino Sans", "TakaoPGothic"):
        try:
            font_manager.findfont(_f, fallback_to_default=False)
            matplotlib.rcParams["font.family"] = [_f]; break
        except Exception:
            continue
import matplotlib.pyplot as plt

def parse(cue):
    body = re.sub(r"^\[GRAPH:?", "", cue).strip().rstrip("]").strip()
    parts = [p.strip() for p in body.split("|")]
    title = parts[0] if parts else ""
    labels, values = [], []
    if len(parts) >= 2:
        for pair in parts[1].split(","):
            if ":" not in pair:
                continue
            k, v = pair.rsplit(":", 1)          # ラベルにコロンが有っても最後の:で値を分離
            vv = re.sub(r"[^0-9.\-]", "", v)
            if not re.search(r"\d", vv):         # 値が数値でない("弱"等)ペアは捨てる＝0バーを出さない
                continue
            try:
                values.append(float(vv)); labels.append(k.strip())
            except ValueError:
                continue
    ylabel = parts[2] if len(parts) >= 3 else ""
    return title, labels, values, ylabel

def main(channel, script_path):
    root = pathlib.Path(__file__).resolve().parents[2]
    gdir = root / "channels" / channel / "out" / "graph"
    gdir.mkdir(parents=True, exist_ok=True)
    cues = [l.strip() for l in open(script_path, encoding="utf-8") if l.strip().startswith("[GRAPH")]
    nodata = 0
    for idx, c in enumerate(cues):
        title, labels, values, ylabel = parse(c)
        fig, ax = plt.subplots(figsize=(16, 9), dpi=120)
        if not labels:                              # 数値データ無し→見出しカード（偽の0/50バーを出さない）
            nodata += 1
            ax.axis("off")
            ax.text(0.5, 0.5, title, ha="center", va="center", fontsize=40, wrap=True)
        else:
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
    msg = f"{len(cues)} graphs -> {gdir}/"
    if nodata:
        msg += f"（うち{nodata}件は数値データ未指定で見出しカードに。台本の[GRAPH:]に『ラベル:数値』を入れると棒グラフになります）"
    print(msg)
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: graph.py <channel> <script.txt>"); sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
