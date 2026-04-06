import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  random,
} from 'remotion';
import {ColorDef} from './LearnColors';
import {MusicNote} from './components/MusicNote';
import {Star} from './components/Star';
import {Sparkle} from './components/Sparkle';
import {Watermark} from './Watermark';

interface ColorSceneProps {
  color: ColorDef;
  sceneIndex: number;
}

export const ColorScene: React.FC<ColorSceneProps> = ({color, sceneIndex}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();

  // ── Scene fade in / out ────────────────────────────────────────────────────
  const fadeIn = interpolate(frame, [0, 12], [0, 1], {extrapolateRight: 'clamp'});
  const fadeOut = interpolate(frame, [fps * 14, fps * 15], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const sceneOpacity = Math.min(fadeIn, fadeOut);

  // ── Title entrance spring ──────────────────────────────────────────────────
  const titleScale = spring({
    frame,
    fps,
    config: {damping: 10, stiffness: 180, mass: 0.6},
    from: 0,
    to: 1,
  });

  // Gentle continuous bounce after entrance (starts after spring settles)
  const continuousBounce =
    frame > fps * 0.6
      ? Math.sin((frame / fps) * Math.PI * 1.6) * 0.04 + 1
      : 1;

  const finalScale = titleScale * continuousBounce;

  // ── Swatch circle entrance ─────────────────────────────────────────────────
  const swatchScale = spring({
    frame: Math.max(0, frame - 8),
    fps,
    config: {damping: 12, stiffness: 200, mass: 0.5},
    from: 0,
    to: 1,
  });

  // ── Floating music notes (8 notes, seeded positions) ──────────────────────
  const notes = Array.from({length: 8}, (_, i) => ({
    x: random(`note-x-${sceneIndex}-${i}`) * (width - 120) + 60,
    baseY: random(`note-y-${sceneIndex}-${i}`) * (height - 120) + 60,
    speed: random(`note-speed-${sceneIndex}-${i}`) * 0.9 + 0.5,
    symbol: i % 2 === 0 ? '♪' : '♫',
    size: random(`note-size-${sceneIndex}-${i}`) * 24 + 28,
    phase: random(`note-phase-${sceneIndex}-${i}`) * Math.PI * 2,
    delayFrames: Math.floor(random(`note-delay-${sceneIndex}-${i}`) * 20),
  }));

  // ── Twinkling stars (14 stars, seeded) ────────────────────────────────────
  const stars = Array.from({length: 14}, (_, i) => ({
    x: random(`star-x-${sceneIndex}-${i}`) * width,
    y: random(`star-y-${sceneIndex}-${i}`) * height,
    size: random(`star-size-${sceneIndex}-${i}`) * 18 + 10,
    phase: random(`star-phase-${sceneIndex}-${i}`) * Math.PI * 2,
    speed: random(`star-speed-${sceneIndex}-${i}`) * 1.5 + 0.8,
  }));

  // ── Sparkle confetti dots (10 dots) ───────────────────────────────────────
  const sparkles = Array.from({length: 10}, (_, i) => ({
    x: random(`sparkle-x-${sceneIndex}-${i}`) * width,
    startY: height + 20,
    size: random(`sparkle-size-${sceneIndex}-${i}`) * 14 + 8,
    speed: random(`sparkle-speed-${sceneIndex}-${i}`) * 0.6 + 0.3,
    phase: random(`sparkle-phase-${sceneIndex}-${i}`) * Math.PI * 2,
    hue: random(`sparkle-hue-${sceneIndex}-${i}`) * 360,
  }));

  // Font family — Comic Sans is charming for kids and always available in Chromium
  const kidFont = "'Comic Sans MS', 'Arial Rounded MT Bold', 'Arial Black', sans-serif";

  return (
    <AbsoluteFill style={{opacity: sceneOpacity}}>
      {/* ── Solid colour background ─────────────────────────────────────── */}
      <AbsoluteFill style={{backgroundColor: color.bg}} />

      {/* ── Twinkling stars ─────────────────────────────────────────────── */}
      {stars.map((star, i) => (
        <Star key={`star-${i}`} {...star} frame={frame} fps={fps} />
      ))}

      {/* ── Rising sparkle confetti ─────────────────────────────────────── */}
      {sparkles.map((s, i) => (
        <Sparkle key={`sparkle-${i}`} {...s} frame={frame} fps={fps} />
      ))}

      {/* ── Centered content ────────────────────────────────────────────── */}
      <AbsoluteFill
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 24,
        }}
      >
        {/* Color name word */}
        <div
          style={{
            fontSize: 148,
            fontWeight: 900,
            fontFamily: kidFont,
            color: color.textColor,
            textShadow: [
              '0 6px 0 rgba(0,0,0,0.25)',
              '0 12px 24px rgba(0,0,0,0.2)',
              '4px 4px 0 rgba(0,0,0,0.15)',
            ].join(', '),
            transform: `scale(${finalScale})`,
            letterSpacing: 6,
            userSelect: 'none',
            lineHeight: 1,
          }}
        >
          {color.name.toUpperCase()}
        </div>

        {/* Colour demonstration circle */}
        <div
          style={{
            width: 110,
            height: 110,
            borderRadius: '50%',
            backgroundColor: 'white',
            border: `8px solid rgba(255,255,255,0.8)`,
            boxShadow: `0 8px 30px rgba(0,0,0,0.25), 0 0 0 4px ${color.bg}`,
            transform: `scale(${swatchScale})`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            overflow: 'hidden',
          }}
        >
          {/* Inner fill shows the actual colour */}
          <div
            style={{
              width: 86,
              height: 86,
              borderRadius: '50%',
              backgroundColor: color.swatchBg,
            }}
          />
        </div>
      </AbsoluteFill>

      {/* ── Floating music notes ─────────────────────────────────────────── */}
      {notes.map((note, i) => (
        <MusicNote key={`note-${i}`} {...note} frame={frame} fps={fps} />
      ))}

      {/* ── Channel watermark ────────────────────────────────────────────── */}
      <Watermark />
    </AbsoluteFill>
  );
};
