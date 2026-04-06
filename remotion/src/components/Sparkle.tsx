import React from 'react';
import {interpolate} from 'remotion';

interface SparkleProps {
  x: number;
  startY: number;
  size: number;
  speed: number;
  phase: number;
  hue: number;
  frame: number;
  fps: number;
}

/**
 * A colourful dot that rises slowly from the bottom of the screen
 * with a gentle horizontal wiggle — like rising bubbles.
 */
export const Sparkle: React.FC<SparkleProps> = ({
  x, startY, size, speed, phase, hue, frame, fps,
}) => {
  const totalDuration = fps * 15; // full scene length

  // Rise from bottom to top over the scene
  const progress = (frame % totalDuration) / totalDuration;
  const y = startY - progress * (startY + 60) * speed;

  // Horizontal wiggle
  const wiggle = Math.sin((frame / fps) * Math.PI * 3 * speed + phase) * 18;

  // Fade in at bottom, fade out near top
  const opacity = interpolate(progress, [0, 0.1, 0.8, 1], [0, 0.8, 0.8, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        left: x + wiggle,
        top: y,
        width: size,
        height: size,
        borderRadius: '50%',
        backgroundColor: `hsl(${hue}, 90%, 65%)`,
        opacity,
        boxShadow: `0 0 ${size}px hsl(${hue}, 90%, 70%)`,
        transform: 'translate(-50%, -50%)',
        pointerEvents: 'none',
      }}
    />
  );
};
