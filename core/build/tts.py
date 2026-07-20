#!/usr/bin/env python3
"""VOICEVOX音声化＋timeline.json生成。

usage: tts.py <channel> <script.txt>

channel_03 の build/tts.py を移植（TODO）。
- 台本を【話者名】単位に分解し、channels/<channel>/speakers.json の
  話者→VOICEVOX話者ID マッピングで音声合成（:50021）
- 連結wav (channels/<channel>/out/voice.wav) と、
  各発話の開始/終了・話者・本文を持つ timeline.json を出力
- タグ [要ファクトチェック]/[GRAPH:]/[IMG:key]/[SHORT候補] は読み上げから除去し、
  timeline側にメタとして残す（Remotionが利用）
"""
import sys

def main(channel: str, script_path: str) -> int:
    raise NotImplementedError("channel_03/build/tts.py を <channel> 対応で移植する")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: tts.py <channel> <script.txt>"); sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
