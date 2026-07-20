#!/usr/bin/env python3
"""台本の [IMG:key]/[OPIMG:]/[EDIMG:] が台帳(assets/irasutoya.json)と
実PNG(core/remotion/public/<channel>/irasutoya/<key>.png)に揃っているか検証。
channel_03(fx-2ch)版を <channel> 引数対応へ移植。立ち絵は [IMG:] sticky 駆動。
usage: check_assets.py <channel> <script.txt>
"""
import sys, re, json, pathlib

def main(channel, script_path):
    root = pathlib.Path(__file__).resolve().parents[2]
    man = json.load(open(root / "channels" / channel / "assets" / "irasutoya.json", encoding="utf-8"))
    keys = {a["key"] for a in man["assets"]}
    imgdir = root / "core" / "remotion" / "public" / channel / "irasutoya"
    used = set()
    for ln in open(script_path, encoding="utf-8"):
        m = re.match(r"\s*\[IMG:\s*([\w-]+)\s*\]", ln)
        if m:
            used.add(m.group(1))
        for tag in ("OPIMG", "EDIMG"):
            mm = re.match(rf"\s*\[{tag}:\s*(.+?)\]", ln)
            if mm:
                used.update(x.strip() for x in mm.group(1).split(",") if x.strip())
    if not used:
        print("注意: 台本に [IMG:] が1つもありません（画像なしで進行します）")
    problems = []
    for k in sorted(used):
        if k not in keys:
            problems.append(f"× 台帳に未登録のキー: [{k}]  → irasutoya.json に追記を")
        elif not (imgdir / f"{k}.png").exists():
            problems.append(f"× PNG未配置: {imgdir}/{k}.png（台帳にはあり）")
    if problems:
        print("\n".join(problems))
        print(f"\n要対応 {len(problems)} 件。素材を用意してから run.sh を実行してください。")
        return 1
    print(f"OK: 使用素材 {len(used)} 件すべて台帳・PNGとも存在。")
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: check_assets.py <channel> <script.txt>"); sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
