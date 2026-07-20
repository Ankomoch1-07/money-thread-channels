# money-thread-channels

2chマネースレ系 自動生成YouTubeチャンネルのモノレポ（共通コア＋チャンネル別）。

- **core/** … 全チャンネル共通のパイプライン（Python build/ ＋ Remotion ＋ news-ingest ＋ run.sh）
- **channels/** … チャンネル固有の設定・プロンプト・素材・ネタ

技術構成はポリグロット：Python(build/, news-ingest/) ＋ Remotion(TS) ＋ run.sh。

## チャンネル

| id | 内容 | 状態 |
|---|---|---|
| channel_03_fx | 2chマネースレ FX版 | 稼働中（Drive→移設予定） |
| channel_04_gold | 2chゴールドスレ（金特化） | 構築中 |

## パイプライン

```
news-ingest(4層収集) → ingest.json → slot_fill → LLM③台本生成 → scripts/epNN.txt
  → 自動QA(qa.py) → LLM内容QA → run.sh(音声/グラフ/レンダ) → 人手ゲート → upload
```

台本DSL（全チャンネル共通・coreの入力契約）:
`【話者名】セリフ` ＋ タグ `[要ファクトチェック]` / `[GRAPH: 内容]` / `[IMG:key]` / `[SHORT候補]`

## 使い方（1本を回す）

```bash
# 1) 時事ネタ収集 → 台本生成（channel_04_gold）
python3 core/news-ingest/build_ingest.py channel_04_gold          # → channels/channel_04_gold/ingest.json
python3 core/news-ingest/slot_fill.py    channel_04_gold ep001    # → channels/channel_04_gold/scripts/ep001.txt

# 2) QA
python3 core/build/qa.py channel_04_gold ep001                    # 自動QA（DSL/尺/NG/ファクト照合）

# 3) レンダ〜完成
core/run.sh channel_04_gold ep001                                 # 音声→グラフ→配置→Remotionレンダ
```

## 設計ドキュメント

設計一式は Drive `Increatism/youtube/channel_04/` に格納：
DESIGN.md / CORE_BOUNDARY.md / script_prompt_v1.1.md / QA.md / NEWS_INGEST.md

## 注意

- Remotionは**ローカルのファイル**を読む。素材はローカルに置いてからレンダ。
- 数値は news-ingest の fact層（価格API取得値）のみを台本へ。LLM創作の数字は使わない。
- 5ch/まとめ/記事本文は**そのまま出力しない**（翻案のみ・flavor層は雰囲気抽出専用）。
