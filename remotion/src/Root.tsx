import React from 'react';
import {Composition} from 'remotion';
import {LearnColors} from './LearnColors';

// 6 colors × 15 seconds × 30 fps = 2700 frames = 90 seconds
const TOTAL_FRAMES = 2700;

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="LearnColors"
      component={LearnColors}
      durationInFrames={TOTAL_FRAMES}
      fps={30}
      width={1280}
      height={720}
    />
  );
};
