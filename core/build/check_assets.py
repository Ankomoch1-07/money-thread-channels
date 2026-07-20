#!/usr/bin/env python3
"""台本の [IMG:key] と 話者デフォルト素材が、素材台帳(assets/irasutoya.json)と
実PNG(core/remotion/public/<channel>/irasutoya/<key>.png)に揃っているか検査。
レンダ前に「存在しない画像参照」を防ぐ。

channel_03/build/check_assets.py を移植。SPEAKER_DEFAULT(話者→既定素材)は
ハードコードをやめ channels/<channel>/theme.json の chara.<name>.img から読む。
台帳 structure は {"assets":[{"key":...}]}。

usage: check_assets.py <channel> <script.txt>
"""
import sys, re, json, pathlib

def main(channel: str, script_path: str) -> int:
    root = pathlib.Path(__file__).resolve().parents[2]
    chdir = root / "channels" / channel
    manifest = json.load(open(chdir / "assets" / "irasutoya.json", encoding="utf-8"))
    imgdir = root / "core" / "remotion" / "public" / channel / "irasutoya"
    theme = json.load(open(chdir / "theme.json", encoding="utf-8"))
    speaker_default = {name: v["img"] for name, v in theme.get("chara", {}).items()}

    keys = {a["key"] for a in manifest["assets"]}
    used = set(speaker_default.values())
    for ln in open(script_path, encoding="utf-8"):
        m = re.match(r"\s*\[IMG:\s*([\w-]+)\s*\]", ln)
        if m:
            used.add(m.group(1))

    problems = []
    for k in sorted(used):
        if k not in keys:
            problems.append(f"× 台帳に未登録のキー: [IMG:{k}]  → irasutoya.json に追記を")
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
