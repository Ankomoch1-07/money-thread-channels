import { Composition, staticFile } from "remotion";
import { Board, Timeline } from "./Board";

// tts.py が channels/<channel>/out/timeline.json を吐き、run.sh で public/<channel>/<ep>/ にコピーする。
const calculateMetadata = async ({ props }: { props: { channel: string; ep: string } }) => {
  const tl: Timeline = await fetch(
    staticFile(`${props.channel}/${props.ep}/timeline.json`)
  ).then((r) => r.json());
  const last = tl.segments[tl.segments.length - 1];
  return {
    durationInFrames: last ? last.start + last.dur : 300,
    fps: tl.fps,
    width: 1920,
    height: 1080,
    props: { ...props, timeline: tl },
  };
};

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Main"
    component={Board as any}
    defaultProps={{ channel: "channel_04_gold", ep: "ep001", timeline: { fps: 30, segments: [] } }}
    calculateMetadata={calculateMetadata as any}
    fps={30}
    width={1920}
    height={1080}
    durationInFrames={300}
  />
);
