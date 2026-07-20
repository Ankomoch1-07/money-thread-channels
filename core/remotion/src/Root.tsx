import { Composition, staticFile } from "remotion";
import { Board, Timeline, Theme } from "./Board";

// channel_03 の Root.tsx を移植。props に channel を追加し、
// タイムライン(<channel>/<ep>/timeline.json)とテーマ(<channel>/theme.json)を読み込む。
type Props = { channel: string; ep: string; timeline: Timeline; theme: Theme };

const calculateMetadata = async ({ props }: { props: { channel: string; ep: string } }) => {
  const [tl, theme]: [Timeline, Theme] = await Promise.all([
    fetch(staticFile(`${props.channel}/${props.ep}/timeline.json`)).then((r) => r.json()),
    fetch(staticFile(`${props.channel}/theme.json`)).then((r) => r.json()),
  ]);
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
