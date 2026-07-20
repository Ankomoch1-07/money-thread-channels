# レンダ手順（channel_04_gold）

## 0. 依存
```bash
brew install node python@3.12                   # ffmpegは不要（tts.pyは標準ライブラリwaveで結合、
                                                #  Remotionはレンダ用ffmpegを内蔵）
cd core/remotion && npm i                        # Remotion 依存（初回のみ）
python3 -m pip install requests matplotlib japanize-matplotlib pillow pyyaml \
        google-api-python-client google-auth-oauthlib
# VOICEVOX ENGINE を :50021 で起動（Docker もしくは VOICEVOXアプリ）
docker run -d --name voicevox -p 50021:50021 voicevox/voicevox_engine:cpu-latest
```
> tts.py は VOICEVOX(:50021) だけ必要。ffmpeg/ffprobe 依存は撤去済み（wave で結合・尺算出）。
> 実測：VOICEVOX 0.25.2 で音声化→Remotionレンダで映像+音声トラック入りmp4を生成できることを確認（2026-07-20）。

## A. 本番パイプライン（音声つき・実レンダ）
```bash
# 台本は channels/channel_04_gold/scripts/<ep>.txt（news-ingest → slot_fill が生成）
python3 core/build/qa.py channel_04_gold <ep>                 # 自動QA
core/run.sh channel_04_gold <ep>                              # 音声→グラフ→配置→Remotionレンダ
# → channels/channel_04_gold/out/<ep>.mp4
```

## B. 映像プレビュー（ffmpeg/VOICEVOX 無しでレイアウト確認）
音声パイプラインを飛ばし、推定尺のtimelineとプレースホルダ素材で映像だけ確認する。
```bash
CH=channel_04_gold; EP=ep_test01; S=channels/$CH/scripts/$EP.txt
python3 core/build/make_placeholder_assets.py $CH             # いらすとや代替＋bg生成（初回）
python3 core/build/timeline_from_script.py $CH $EP $S         # 推定尺 timeline.json
python3 core/build/graph.py $CH $S
cp channels/$CH/out/graph/*.png core/remotion/public/$CH/$EP/graph/ 2>/dev/null
cp channels/$CH/theme.json core/remotion/public/$CH/theme.json
cd core/remotion
npx remotion still src/index.ts Main /tmp/frame.png --frame=200 --props="{\"channel\":\"$CH\",\"ep\":\"$EP\"}"
npx remotion studio src/index.ts                             # ブラウザでプレビュー（props で channel/ep 指定）
```
検証済み：この手順で still_board.png / still_graph.png が正しくレンダされることを確認（2026-07-20）。

## 素材（public は gitignore＝各自 procure/generate）
- プレースホルダ：`make_placeholder_assets.py`（検証用）
- 実運用：いらすとや実素材を `core/remotion/public/channel_04_gold/irasutoya/<key>.png` に配置
  （key は `channels/channel_04_gold/assets/irasutoya.json` と `theme.json` の chara.img）
- 背景：`core/remotion/public/channel_04_gold/bg/gold.mp4`（動画）。用意でき次第 `theme.json` の
  `bg` を `bg/gold.mp4` に戻す（現在はプレースホルダ `bg/gold.png`）。
