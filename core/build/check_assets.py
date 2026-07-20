#!/usr/bin/env python3
"""[IMG:key] と素材台帳(assets/irasutoya.json)の整合チェック。

usage: check_assets.py <channel> <script.txt>

channel_03 の build/check_assets.py を <channel> 引数対応に一般化して移植する（TODO）。
- 台本内の [IMG:key] を全抽出
- channels/<channel>/assets/irasutoya.json の key と突き合わせ
- 未登録 key があれば非0で終了（run.sh を止める）
"""
import sys, json, re, pathlib

def main(channel: str, script_path: str) -> int:
    root = pathlib.Path(__file__).resolve().parents[2]
    catalog_path = root / "channels" / channel / "assets" / "irasutoya.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8")) if catalog_path.exists() else {}
    text = pathlib.Path(script_path).read_text(encoding="utf-8")
    keys = re.findall(r"\[IMG:([^\]]+)\]", text)
    missing = [k for k in keys if k not in catalog]
    if missing:
        print(f"[check_assets] 未登録の素材key: {sorted(set(missing))}")
        return 1
    print(f"[check_assets] OK ({len(set(keys))} keys)")
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: check_assets.py <channel> <script.txt>"); sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
