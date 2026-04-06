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

  // Float vertically using a sine wave
  const floatOffset = Math.sin((adjustedFrame / fps) * Math.PI * 2 * speed + phase) * 28;

  // Gentle rotation sway
  const rotation = Math.sin((adjustedFrame / fps) * Math.PI * speed + phase) * 14;

  // Fade in on entrance
  const opacity = interpolate(adjustedFrame, [0, 12], [0, 0.85], {extrapolateRight: 'clamp'});

  // Subtle scale pulse
  const scalePulse = 1 + Math.sin((adjustedFrame / fps) * Math.PI * 2.2 + phase) * 0.06;

  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: baseY + floatOffset,
        fontSize: size,
        opacity,
        transform: `translate(-50%, -50%) rotate(${rotation}deg) scale(${scalePulse})`,
        color: 'rgba(255, 255, 255, 0.88)',
        textShadow: '2px 2px 6px rgba(0,0,0,0.35)',
        userSelect: 'none',
        pointerEvents: 'none',
      }}
    >
      {symbol}
    </div>
  );
};
