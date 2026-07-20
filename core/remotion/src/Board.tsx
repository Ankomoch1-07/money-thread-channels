// 2ch掲示板UIの描画エンジン（channel_03 の src/Board.tsx を移植する TODO）
// theme をチャンネル別に注入できるようにするのが channel_04 での唯一の変更点。
// - timeline.json（tts.py出力）を読み、話者ごとのレスを順に表示
// - [GRAPH:] は public/<channel>/<ep>/graph/*.png、[IMG:key] はいらすとやPNGを重ねる
// - theme: ゴールド基調（accent #D4AF37）＋背景。channels/<channel>/theme.json から供給
import {z} from "zod";

export const boardSchema = z.object({
  channel: z.string(),
  ep: z.string(),
});

export const Board: React.FC<z.infer<typeof boardSchema>> = ({channel, ep}) => {
  // TODO: timeline.json / theme.json を読み込み、レス掛け合いを描画
  return null;
};
