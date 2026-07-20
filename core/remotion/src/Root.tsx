// Remotion Root（channel_03 の src/Root.tsx を theme props 対応で移植する TODO）
// props で channel/ep を受け取り、channels/<channel>/theme.json の色・背景を Board に注入する。
import {Composition} from "remotion";
import {Board, boardSchema} from "./Board";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Main"
      component={Board}
      durationInFrames={300}      // TODO: timeline.json から算出
      fps={30}
      width={1920}
      height={1080}
      schema={boardSchema}
      defaultProps={{channel: "channel_04_gold", ep: "ep001"}}
    />
  );
};
