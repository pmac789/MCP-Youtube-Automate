import React from 'react';
import {AbsoluteFill, staticFile} from 'remotion';
import {Audio} from '@remotion/media';
import {TransitionSeries, linearTiming} from '@remotion/transitions';
import {fade} from '@remotion/transitions/fade';
import {ColorScene} from './ColorScene';
import {SCENE_FRAMES, TRANSITION_FRAMES} from './Root';

export interface ColorDef {
  name: string;
  /** The actual colour value — used for text colour and accent shapes. */
  hex: string;
  /** Lighter tint used for the backdrop blob behind the word. */
  blobHex: string;
}

// Each colour: vivid hex for text + a lighter/softer tint for the bg blob.
export const COLORS: ColorDef[] = [
  {name: 'Red',    hex: '#E8000D', blobHex: '#FFB3B8'},
  {name: 'Yellow', hex: '#E6A800', blobHex: '#FFF0A0'},
  {name: 'Blue',   hex: '#005FCC', blobHex: '#B3D4FF'},
  {name: 'Green',  hex: '#007A24', blobHex: '#B3F0C8'},
  {name: 'Purple', hex: '#7B00CC', blobHex: '#DDB3FF'},
  {name: 'Orange', hex: '#CC5500', blobHex: '#FFD4A0'},
];

export const LearnColors: React.FC = () => {
  return (
    // Sky blue base — constant throughout the whole video
    <AbsoluteFill style={{backgroundColor: '#7BC8F6'}}>
      {/* Audio — copy ../output/audio.mp3 to public/audio.mp3 before rendering */}
      <Audio src={staticFile('audio.mp3')} />

      <TransitionSeries>
        {COLORS.map((color, i) => (
          <React.Fragment key={color.name}>
            <TransitionSeries.Sequence
              durationInFrames={SCENE_FRAMES}
              // premount so font + assets are ready before the scene becomes visible
            >
              <ColorScene color={color} sceneIndex={i} />
            </TransitionSeries.Sequence>

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
