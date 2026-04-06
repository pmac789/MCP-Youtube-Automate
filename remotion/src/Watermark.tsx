import React from 'react';
import {loadFont} from '@remotion/google-fonts/Nunito';

const {fontFamily} = loadFont('normal', {weights: ['700'], subsets: ['latin']});

export const Watermark: React.FC = () => (
  <div
    style={{
      position: 'absolute',
      bottom: 18,
      right: 22,
      color: 'rgba(255, 255, 255, 0.62)',
      fontSize: 22,
      fontFamily,
      fontWeight: 700,
      textShadow: '1px 1px 4px rgba(0,0,0,0.45)',
      userSelect: 'none',
      pointerEvents: 'none',
      letterSpacing: 1,
    }}
  >
    Happy Melody Kids
  </div>
);
