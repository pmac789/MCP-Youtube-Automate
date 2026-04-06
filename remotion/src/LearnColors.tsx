import React from 'react';
import {AbsoluteFill, Audio, Sequence, staticFile} from 'remotion';
import {ColorScene} from './ColorScene';

export interface ColorDef {
  name: string;
  bg: string;        // background fill for the whole scene
  textColor: string; // color of the word itself
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

const SCENE_FRAMES = 450; // 15 seconds × 30 fps

export const LearnColors: React.FC = () => {
  // audio.mp3 must be copied to remotion/public/ before rendering
  // (the render-colors.sh script handles this automatically)
  const hasAudio = true;

  return (
    <AbsoluteFill style={{backgroundColor: '#7BC8F6'}}>
      {hasAudio && (
        <Audio src={staticFile('audio.mp3')} />
      )}

      {COLORS.map((color, i) => (
        <Sequence
          key={color.name}
          from={i * SCENE_FRAMES}
          durationInFrames={SCENE_FRAMES}
        >
          <ColorScene color={color} sceneIndex={i} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
