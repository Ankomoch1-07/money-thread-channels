#!/usr/bin/env python3
"""台本の [GRAPH:...] 行を拾って解説グラフPNGを channels/<channel>/out/graph/NN.png に出力。

channel_03 版はFX例(2%/10%リスク)を固定描画していたが、コメントにあった
[GRAPH: type=bar; x=..; y=..; ylabel=..; title=..] のパースを実装して汎用化した。
構造化データが無い [GRAPH: 自由記述] はタイトルカード(説明文の見出し)として描画する。
実データ(fact/reference由来)は slot_fill が [GRAPH: ...] に埋め込む想定。

usage: graph.py <channel> <script.txt>
"""
import re, sys, os, pathlib
import matplotlib.pyplot as plt
import japanize_matplotlib  # noqa: F401  (日本語フォント有効化)

def parse_kv(body: str) -> dict:
    """'type=bar; x=a,b; y=1,2; ylabel=..; title=..' → dict"""
    out = {}
    for part in body.split(";"):
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        out[k.strip()] = v.strip()
    return out

def draw_bar(ax, kv):
    x = [s.strip() for s in kv.get("x", "").split(",") if s.strip()]
    y = [float(s) for s in kv.get("y", "").split(",") if s.strip()]
    ax.bar(x, y, color=["#c9a227", "#8a1b1b", "#0b63c4", "#1b8a3a"][: len(x)] or None)
    ax.set_ylabel(kv.get("ylabel", ""), fontsize=20)
    for i, v in enumerate(y):
        ax.text(i, v, f"{v:g}", ha="center", va="bottom", fontsize=24)

def draw_title_card(ax, text):
    ax.axis("off")
    ax.text(0.5, 0.5, text, ha="center", va="center", fontsize=34, wrap=True)

def main(channel: str, script_path: str) -> int:
    root = pathlib.Path(__file__).resolve().parents[2]
    gdir = root / "channels" / channel / "out" / "graph"
    gdir.mkdir(parents=True, exist_ok=True)
    cues = [l.strip() for l in open(script_path, encoding="utf-8")
            if l.strip().startswith("[GRAPH")]

    for idx, c in enumerate(cues):
        body = re.sub(r"^\[GRAPH:?", "", c).strip("] \n")
        kv = parse_kv(body)
        fig, ax = plt.subplots(figsize=(16, 9), dpi=120)
        if kv.get("type") == "bar" and kv.get("x") and kv.get("y"):
            draw_bar(ax, kv)
            ax.set_title(kv.get("title", ""), fontsize=28)
        else:
            draw_title_card(ax, body)   # 自由記述はタイトルカード
        fig.savefig(gdir / f"{idx:02d}.png", bbox_inches="tight")
        plt.close(fig)

    print(f"{len(cues)} graphs -> {gdir}/")
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: graph.py <channel> <script.txt>"); sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
