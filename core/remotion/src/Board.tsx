import {
  AbsoluteFill, Audio, Img, OffthreadVideo, staticFile, useCurrentFrame, interpolate,
} from "remotion";
import React from "react";

export type Seg = {
  i: number; name: string; text: string;
  start: number; dur: number; graph: number | null; img?: string | null;
};
export type Timeline = { fps: number; title?: string; segments: Seg[] };
export type Chara = Record<string, { color: string; img: string }>;
export type Theme = {
  bg: string; titleBg?: string; titleColor?: string; chara: Chara; narrator?: string;
};

// channel_03 の Board.tsx を移植。ハードコードだった CHARA(キャラ色/素材)・背景・タイトル色を
// theme(props) に外出しし、素材パスを channel 別(<channel>/...)にした。
// 話者→レス枠の色/いらすとやは theme.chara、[IMG:key] 指定があれば seg.img が優先。
export const Board: React.FC<{ channel: string; ep: string; timeline: Timeline; theme: Theme }> = ({
  channel, ep, timeline, theme,
}) => {
  const frame = useCurrentFrame();
  const segs = timeline.segments;
  const idx = Math.max(0, segs.findIndex((s) => frame < s.start + s.dur));
  const cur = segs[idx] ?? segs[segs.length - 1];
  const visible = segs.slice(Math.max(0, idx - 2), idx + 1); // 直近3レスを左上に積む
  const imgKey = cur?.img ?? theme.chara[cur?.name ?? ""]?.img;

  return (
    <AbsoluteFill style={{ fontFamily: "sans-serif" }}>
      {/* 背景：チャンネル別の動画素材（例 public/<channel>/bg/gold.mp4） */}
      <OffthreadVideo
        src={staticFile(`${channel}/${theme.bg}`)} muted loop
        style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }}
      />
      <Audio src={staticFile(`${channel}/${ep}/voice.wav`)} />

      {/* 右上：スレタイ帯 */}
      <div style={{
        position: "absolute", top: 0, right: 0, maxWidth: 1260,
        background: theme.titleBg ?? "rgba(18,22,30,.9)", color: theme.titleColor ?? "#fff",
        padding: "21px 38px 21px 58px", fontSize: 36, fontWeight: 700,
        clipPath: "polygon(46px 0, 100% 0, 100% 100%, 0 100%)", whiteSpace: "nowrap",
      }}>
        {timeline.title ?? ""}
      </div>

      {/* 右下：いらすとや素材（話者/場面で差替） */}
      {imgKey && (
        <Img
          src={staticFile(`${channel}/irasutoya/${imgKey}.png`)}
          style={{ position: "absolute", right: 77, bottom: 0, height: 691 }}
        />
      )}

      {/* 左：レス吹き出し（上から下へ・左寄せ・名前なし・話者色枠） */}
      <div style={{
        position: "absolute", left: 58, top: 96, width: 922,
        display: "flex", flexDirection: "column", gap: 23,
      }}>
        {visible.map((s) => (
          <div key={s.i} style={{
            background: "#fff", borderRadius: 19, padding: "23px 31px",
            border: `7px solid ${theme.chara[s.name]?.color ?? "#333"}`,
            boxShadow: "0 7px 17px rgba(0,0,0,.28)",
            fontSize: 40, fontWeight: 700, lineHeight: 1.36, color: "#111",
            alignSelf: "flex-start",
          }}>
            {s.text}
          </div>
        ))}
      </div>

      {/* 解説グラフのフルスクリーン差し込み */}
      {cur?.graph != null && (
        <AbsoluteFill style={{
          background: "rgba(12,20,14,.93)", alignItems: "center", justifyContent: "center",
          opacity: interpolate(frame - cur.start, [0, 10], [0, 1], { extrapolateRight: "clamp" }),
        }}>
          <Img
            src={staticFile(`${channel}/${ep}/graph/${String(cur.graph).padStart(2, "0")}.png`)}
            style={{ width: 1498, borderRadius: 19, background: "#fff", padding: 25 }}
          />
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
