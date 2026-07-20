#!/bin/bash
# 使い方: core/run.sh <channel> <ep>
#   例:   core/run.sh channel_04_gold ep001
# 前提: VOICEVOX(Docker)が :50021 で起動中 / core/remotion/ は npm i 済み
# channel_03(FX版)の run.sh を <channel> 引数対応に一般化したもの。
set -e
CH=$1
EP=$2
[ -z "$CH" ] || [ -z "$EP" ] && { echo "usage: core/run.sh <channel> <ep>"; exit 1; }

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CHDIR="$ROOT/channels/$CH"
SCRIPT="$CHDIR/scripts/$EP.txt"
[ -f "$SCRIPT" ] || { echo "not found: $SCRIPT"; exit 1; }

echo "▶ 0/4 素材チェック（$CH）"
python3 "$ROOT/core/build/check_assets.py" "$CH" "$SCRIPT"
echo "▶ 1/4 音声＋タイムライン生成"
python3 "$ROOT/core/build/tts.py"          "$CH" "$SCRIPT"
echo "▶ 2/4 解説グラフ生成"
python3 "$ROOT/core/build/graph.py"        "$CH" "$SCRIPT"

echo "▶ 3/4 素材をRemotionのpublicへ配置"
PUB="$ROOT/core/remotion/public/$CH"
DEST="$PUB/$EP"
mkdir -p "$DEST/graph"
cp "$CHDIR/out/voice.wav"     "$DEST/voice.wav"
cp "$CHDIR/out/timeline.json" "$DEST/timeline.json"
cp "$CHDIR/out/graph/"*.png   "$DEST/graph/" 2>/dev/null || true
cp "$CHDIR/theme.json"        "$PUB/theme.json"          # テーマ(色/背景/配役)
# ※ 静的素材は初回に一度だけ配置しておく（使い回し）:
#     $PUB/irasutoya/<key>.png   … いらすとや（台帳 assets/irasutoya.json の key）
#     $PUB/bg/gold.mp4           … 背景動画（theme.json の bg）

echo "▶ 4/4 Remotionレンダ → $CHDIR/out/$EP.mp4"
# 背景は毎回2本使う（OP/ED用＋中身用）。public/<ch>/bg/ の *.mp4 プールからランダムに2本選ぶ
# （"格納しておくだけ"でランダム）。無ければ静止画にフォールバック。透明度はtheme.jsonのbgOpacity(既定0.8)。
shopt -s nullglob
BGS=( "$PUB"/bg/*.mp4 "$PUB"/bg/*.mov "$PUB"/bg/*.webm )   # 動画は mp4/mov/webm を候補に
[ ${#BGS[@]} -eq 0 ] && BGS=( "$PUB"/bg/*.png )
OPED=""; MAIN=""
N=${#BGS[@]}
if [ "$N" -gt 0 ]; then
  I=$(( RANDOM % N ))
  if [ "$N" -gt 1 ]; then J=$(( (I + 1 + RANDOM % (N - 1)) % N )); else J=$I; fi   # 中身は別の1本
  OPED="bg/$(basename "${BGS[$I]}")"; MAIN="bg/$(basename "${BGS[$J]}")"
  echo "  背景2本選択: OP/ED=$OPED / 中身=$MAIN（候補${N}本）"
fi
( cd "$ROOT/core/remotion" && npx remotion render src/index.ts Main "../../channels/$CH/out/$EP.mp4" \
    --props="{\"channel\":\"$CH\",\"ep\":\"$EP\",\"bgOpEd\":\"$OPED\",\"bgMain\":\"$MAIN\"}" )

echo "✅ 完成: channels/$CH/out/$EP.mp4"
echo "   → 人手ゲート: [要ファクトチェック]数値・冒頭30秒・サムネ(vidIQ)を確認し upload.py で予約投稿"
