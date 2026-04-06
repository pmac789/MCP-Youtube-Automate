import React from 'react';
import {interpolate} from 'remotion';

interface MusicNoteProps {
  x: number;
  baseY: number;
  speed: number;
  symbol: string;
  size: number;
  phase: number;
  delayFrames: number;
  frame: number;
  fps: number;
}

export const MusicNote: React.FC<MusicNoteProps> = ({
  x, baseY, speed, symbol, size, phase, delayFrames, frame, fps,
}) => {
  const adjustedFrame = Math.max(0, frame - delayFrames);

  // Float on a sine wave
  const floatY = Math.sin((adjustedFrame / fps) * Math.PI * 2 * speed + phase) * 30;

  // Gentle rotation sway
  const rotation = Math.sin((adjustedFrame / fps) * Math.PI * speed * 0.7 + phase) * 16;

  // Fade in on entrance
  const opacity = interpolate(adjustedFrame, [0, 14], [0, 0.88], {
    extrapolateRight: 'clamp',
  });

  // Subtle scale pulse
  const scale = 1 + Math.sin((adjustedFrame / fps) * Math.PI * 2.4 + phase) * 0.07;

  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: baseY + floatY,
        fontSize: size,
        opacity,
        transform: `translate(-50%, -50%) rotate(${rotation}deg) scale(${scale})`,
        color: 'white',
        textShadow: '2px 2px 0 rgba(0,0,0,0.25), 0 0 12px rgba(255,255,255,0.5)',
        userSelect: 'none',
        pointerEvents: 'none',
      }}
    >
      {symbol}
    </div>
  );
};
