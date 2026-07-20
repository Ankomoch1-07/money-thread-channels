import { Composition, staticFile } from "remotion";
import { Board, Timeline, Theme } from "./Board";

// channel_03 の Root.tsx を移植。props に channel を追加し、
// タイムライン(<channel>/<ep>/timeline.json)とテーマ(<channel>/theme.json)を読み込む。
type Props = {
  channel: string; ep: string; bgOpEd?: string; bgMain?: string; timeline: Timeline; theme: Theme;
};

const calculateMetadata = async ({ props }: { props: { channel: string; ep: string; bgOpEd?: string; bgMain?: string } }) => {
  const [tl, theme]: [Timeline, Theme] = await Promise.all([
    fetch(staticFile(`${props.channel}/${props.ep}/timeline.json`)).then((r) => r.json()),
    fetch(staticFile(`${props.channel}/theme.json`)).then((r) => r.json()),
  ]);
  // 背景：毎回2本使う（OP/ED用＋中身用）。run.shが渡した props を最優先、無ければ theme.bgs から
  // ep名シードで決定論的に2本選ぶ（プールが2本以上なら別々の動画に）。Math.random不使用でチラつき回避。
  const pool = theme.bgs && theme.bgs.length ? theme.bgs : [theme.bg];
  const seed = (props.ep || "").split("").reduce((a, c) => a + c.charCodeAt(0), 0);
  theme.bgOpEd = props.bgOpEd || pool[seed % pool.length];
  theme.bgMain = props.bgMain || pool[(seed + 1) % pool.length];
  const last = tl.segments[tl.segments.length - 1];
  return {
    durationInFrames: last ? last.start + last.dur : 300,
    fps: tl.fps,
    width: 1920,
    height: 1080,
    props: { ...props, timeline: tl, theme } as Props,
  };
};

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Main"
    component={Board as any}
    defaultProps={{
      channel: "channel_04_gold",
      ep: "ep001",
      timeline: { fps: 30, segments: [] },
      theme: { bg: "bg/gold.mp4", chara: {} },
    } as Props}
    calculateMetadata={calculateMetadata as any}
    fps={30}
    width={1920}
    height={1080}
    durationInFrames={300}
  />
);
