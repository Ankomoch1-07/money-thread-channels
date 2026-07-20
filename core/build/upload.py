#!/usr/bin/env python3
"""YouTube Data API v3 で予約投稿。

usage: upload.py <channel> <mp4> <title> <description> <publishAt(ISO8601)>

channel_03 の build/upload.py を移植（TODO）。
- channels/<channel>/build/client_secret.json / token.json でOAuth（初回のみブラウザ認証）
- 概要欄にフィクション明記を付与
- 長尺→数時間後にショート、の二段投稿は将来のスケジューラで
"""
import sys

def main(argv) -> int:
    raise NotImplementedError("channel_03/build/upload.py を <channel> 対応で移植する")

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("usage: upload.py <channel> <mp4> <title> <description> <publishAt>"); sys.exit(2)
    sys.exit(main(sys.argv[1:]))
