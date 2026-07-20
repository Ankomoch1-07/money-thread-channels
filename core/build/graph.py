#!/usr/bin/env python3
"""[GRAPH: 内容] を matplotlib で画像化。

usage: graph.py <channel> <script.txt>

channel_03 の build/graph.py を移植（TODO）。
- 台本内の [GRAPH: 内容] を全抽出し、内容に応じた図を生成
- channels/<channel>/out/graph/NN.png として保存（run.sh が public へ配置）
- 金特化の想定グラフ：実質金利 vs 金価格 / 中央銀行金購入量 / 長期チャート /
  一括 vs 積立の平均取得単価 など。データは fact/reference 由来を差し込む
- japanize-matplotlib で日本語ラベル対応
"""
import sys

def main(channel: str, script_path: str) -> int:
    raise NotImplementedError("channel_03/build/graph.py を <channel> 対応で移植する")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: graph.py <channel> <script.txt>"); sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
