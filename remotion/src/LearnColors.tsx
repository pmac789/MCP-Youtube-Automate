import React from 'react';
import {AbsoluteFill, staticFile} from 'remotion';
import {Audio} from '@remotion/media';
import {TransitionSeries, linearTiming} from '@remotion/transitions';
import {fade} from '@remotion/transitions/fade';
import {ColorScene} from './ColorScene';
import {SCENE_FRAMES, TRANSITION_FRAMES} from './Root';

export interface ColorDef {
  name: string;
  bg: string;        // background fill for the whole scene
  textColor: string; // color of the word text
  swatchBg: string;  // inner fill of the demonstration circle
}

export const COLORS: ColorDef[] = [
  {name: 'Red',    bg: '#FF3B3B', textColor: '#FFFFFF', swatchBg: '#FF3B3B'},
  {name: 'Yellow', bg: '#FFD93D', textColor: '#333333', swatchBg: '#FFD93D'},
  {name: 'Blue',   bg: '#2E9BFF', textColor: '#FFFFFF', swatchBg: '#2E9BFF'},
  {name: 'Green',  bg: '#3DBE5B', textColor: '#FFFFFF', swatchBg: '#3DBE5B'},
  {name: 'Purple', bg: '#9B30D9', textColor: '#FFFFFF', swatchBg: '#9B30D9'},
  {name: 'Orange', bg: '#FF8C00', textColor: '#FFFFFF', swatchBg: '#FF8C00'},
];

export const LearnColors: React.FC = () => {
  return (
    <AbsoluteFill style={{backgroundColor: '#7BC8F6'}}>
      {/* Audio — copy ../output/audio.mp3 to public/audio.mp3 before rendering */}
      <Audio src={staticFile('audio.mp3')} />

      {/*
        TransitionSeries shortens the total timeline by the transition duration
        for each cut, so TOTAL_FRAMES is already calculated correctly in Root.tsx.
      */}
      <TransitionSeries>
        {COLORS.map((color, i) => (
          <React.Fragment key={color.name}>
            <TransitionSeries.Sequence durationInFrames={SCENE_FRAMES}>
              <ColorScene color={color} sceneIndex={i} />
            </TransitionSeries.Sequence>

            {/* No transition after the last scene */}
            {i < COLORS.length - 1 && (
              <TransitionSeries.Transition
                presentation={fade()}
                timing={linearTiming({durationInFrames: TRANSITION_FRAMES})}
              />
            )}
          </React.Fragment>
        ))}
      </TransitionSeries>
    </AbsoluteFill>
  );
};
