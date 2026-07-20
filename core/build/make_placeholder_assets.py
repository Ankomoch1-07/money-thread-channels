#!/usr/bin/env python3
"""レンダ検証用のプレースホルダ素材を生成する（実いらすとや素材の代替）。

台帳(assets/irasutoya.json)の全keyについて core/remotion/public/<channel>/irasutoya/<key>.png を、
背景 public/<channel>/bg/gold.png を生成する。これで check_assets が通り、実素材が無くても
Remotionレンダを最後まで通して動作確認できる。実運用ではいらすとや実素材に差し替える。

usage: make_placeholder_assets.py <channel>
"""
import sys, json, pathlib
from PIL import Image, ImageDraw

def label_png(path: pathlib.Path, text: str, color: str, size=(600, 760)):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    w, h = size
    d.rounded_rectangle([20, 20, w - 20, h - 20], radius=40, fill=color, outline="#ffffff", width=8)
    d.text((w // 2, h // 2), text, fill="#ffffff", anchor="mm")
    img.save(path)

def bg_png(path: pathlib.Path, title: str, size=(1920, 1080)):
    img = Image.new("RGB", size, (24, 20, 10))
    d = ImageDraw.Draw(img)
    for y in range(size[1]):                       # 縦グラデ（ゴールド基調）
        t = y / size[1]
        d.line([(0, y), (size[0], y)],
               fill=(int(40 + 60 * t), int(32 + 44 * t), int(12 + 10 * t)))
    d.text((size[0] // 2, size[1] // 2), title, fill="#D4AF37", anchor="mm")
    img.save(path)

def main(channel: str) -> int:
    root = pathlib.Path(__file__).resolve().parents[2]
    chdir = root / "channels" / channel
    manifest = json.load(open(chdir / "assets" / "irasutoya.json", encoding="utf-8"))
    theme = json.load(open(chdir / "theme.json", encoding="utf-8"))
    color_of = {v["img"]: v["color"] for v in theme.get("chara", {}).values()}
    pub = root / "core" / "remotion" / "public" / channel
    (pub / "irasutoya").mkdir(parents=True, exist_ok=True)
    (pub / "bg").mkdir(parents=True, exist_ok=True)

    made = 0
    for a in manifest["assets"]:
        k = a["key"]
        p = pub / "irasutoya" / f"{k}.png"
        if p.exists():
            continue        # 既存(実素材含む)は上書きしない＝安全に再実行できる
        label_png(p, f"{k}\n(placeholder)", color_of.get(k, "#8a6d1f"))
        made += 1
    bgp = pub / "bg" / "gold.png"
    if not bgp.exists():
        bg_png(bgp, channel)
    print(f"生成: 不足していた {made} 素材PNGのみ補完 → {pub}/irasutoya")
    print("※ プレースホルダです。実運用ではいらすとや実素材に差し替えてください。")
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: make_placeholder_assets.py <channel>"); sys.exit(2)
    sys.exit(main(sys.argv[1]))
