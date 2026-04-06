import React from 'react';
import {interpolate} from 'remotion';

interface StarProps {
  x: number;
  y: number;
  size: number;
  phase: number;
  speed: number;
  frame: number;
  fps: number;
}

export const Star: React.FC<StarProps> = ({x, y, size, phase, speed, frame, fps}) => {
  // Twinkle: sinusoidal opacity and scale
  const t = (frame / fps) * Math.PI * 2 * speed + phase;
  const twinkle = (Math.sin(t) + 1) / 2; // 0 → 1

  const opacity = interpolate(twinkle, [0, 1], [0.25, 0.95]);
  const scale = interpolate(twinkle, [0, 1], [0.6, 1.4]);

  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y,
        fontSize: size,
        opacity,
        transform: `translate(-50%, -50%) scale(${scale})`,
        userSelect: 'none',
        color: 'rgba(255, 255, 180, 0.9)',
        textShadow: '0 0 8px rgba(255,255,100,0.8)',
        pointerEvents: 'none',
      }}
    >
      ★
    </div>
  );
};
