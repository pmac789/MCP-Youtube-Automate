import React from 'react';
import {Composition} from 'remotion';
import {LearnColors} from './LearnColors';

// 6 scenes × 450 frames = 2700
// minus 5 transitions × 15 frames overlap = 75
// total = 2625 frames = 87.5 seconds
export const SCENE_FRAMES = 450;      // 15s per color at 30fps
export const TRANSITION_FRAMES = 15;  // 0.5s crossfade

const COLOR_COUNT = 6;
const TOTAL_FRAMES =
  COLOR_COUNT * SCENE_FRAMES - (COLOR_COUNT - 1) * TRANSITION_FRAMES;

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
