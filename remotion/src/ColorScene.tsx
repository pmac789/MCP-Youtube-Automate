import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  random,
  Easing,
} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Nunito';
import {ColorDef} from './LearnColors';
import {MusicNote} from './components/MusicNote';
import {Star} from './components/Star';
import {Sparkle} from './components/Sparkle';
import {Watermark} from './Watermark';

// Loaded once at module level — Remotion blocks rendering until the font is ready.
const {fontFamily} = loadFont('normal', {
  weights: ['900'],
  subsets: ['latin'],
});

interface ColorSceneProps {
  color: ColorDef;
  sceneIndex: number;
}

export const ColorScene: React.FC<ColorSceneProps> = ({color, sceneIndex}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();

  // ── Blob entrance: slides up from below with easing ───────────────────────
  const blobEntrance = interpolate(
    frame,
    [0, 25],
    [120, 0],
    {
      extrapolateRight: 'clamp',
      easing: Easing.out(Easing.exp),
    }
  );
  const blobScale = spring({
    frame,
    fps,
    config: {damping: 10, stiffness: 160},
    durationInFrames: 30,
  });

  // ── Word bounce-in ─────────────────────────────────────────────────────────
  // Per skill: {damping: 8} = bouncy entrance
  const wordScale = spring({
    frame,
    fps,
    config: {damping: 8},
    durationInFrames: 40,
    from: 0,
    to: 1,
  });

  // Continuous gentle bob after spring settles (frame > ~40)
  const bob = frame > 38
    ? Math.sin((frame / fps) * Math.PI * 1.8) * 0.032 + 1
    : 1;

  const finalWordScale = wordScale * bob;

  // ── Colour circle that pulses in the bottom half ───────────────────────────
  const circlePulse = 1 + Math.sin((frame / fps) * Math.PI * 2.4) * 0.05;
  const circleScale = spring({
    frame,
    fps,
    config: {damping: 8},
    durationInFrames: 35,
    delay: 10,
    from: 0,
    to: 1,
  }) * circlePulse;

  // ── Seeded floating music notes (8) ───────────────────────────────────────
  const notes = Array.from({length: 8}, (_, i) => ({
    x: random(`note-x-${sceneIndex}-${i}`) * (width - 140) + 70,
    baseY: random(`note-y-${sceneIndex}-${i}`) * (height - 140) + 70,
    speed: random(`note-speed-${sceneIndex}-${i}`) * 0.9 + 0.5,
    symbol: i % 2 === 0 ? '♪' : '♫',
    size: random(`note-size-${sceneIndex}-${i}`) * 28 + 32,
    phase: random(`note-phase-${sceneIndex}-${i}`) * Math.PI * 2,
    delayFrames: Math.floor(random(`note-delay-${sceneIndex}-${i}`) * 18),
  }));

  // ── Seeded twinkling stars (16) ───────────────────────────────────────────
  const stars = Array.from({length: 16}, (_, i) => ({
    x: random(`star-x-${sceneIndex}-${i}`) * width,
    y: random(`star-y-${sceneIndex}-${i}`) * height,
    size: random(`star-size-${sceneIndex}-${i}`) * 22 + 10,
    phase: random(`star-phase-${sceneIndex}-${i}`) * Math.PI * 2,
    speed: random(`star-speed-${sceneIndex}-${i}`) * 1.6 + 0.7,
  }));

  // ── Rising sparkle bubbles (12) ───────────────────────────────────────────
  const sparkles = Array.from({length: 12}, (_, i) => ({
    x: random(`sparkle-x-${sceneIndex}-${i}`) * width,
    startY: height + 20,
    size: random(`sparkle-size-${sceneIndex}-${i}`) * 16 + 8,
    speed: random(`sparkle-speed-${sceneIndex}-${i}`) * 0.55 + 0.3,
    phase: random(`sparkle-phase-${sceneIndex}-${i}`) * Math.PI * 2,
    hue: random(`sparkle-hue-${sceneIndex}-${i}`) * 360,
  }));

  // Adaptive font size so the word always fits comfortably
  const charCount = color.name.length;
  const maxFontSize = 190;
  const fontSize = charCount > 5
    ? Math.round(maxFontSize * (5 / charCount))
    : maxFontSize;

  return (
    <AbsoluteFill>
      {/* Sky blue bg is inherited from LearnColors — nothing to set here */}

      {/* ── Soft colour blob behind the word ───────────────────────────── */}
      <AbsoluteFill
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div
          style={{
            width: 780,
            height: 320,
            borderRadius: 160,
            backgroundColor: color.blobHex,
            opacity: 0.82,
            transform: `translateY(${blobEntrance}px) scale(${blobScale})`,
            boxShadow: `0 12px 60px ${color.hex}44`,
          }}
        />
      </AbsoluteFill>

      {/* ── Twinkling stars ─────────────────────────────────────────────── */}
      {stars.map((star, i) => (
        <Star key={`star-${i}`} {...star} frame={frame} fps={fps} />
      ))}

      {/* ── Rising sparkle bubbles ──────────────────────────────────────── */}
      {sparkles.map((s, i) => (
        <Sparkle key={`sparkle-${i}`} {...s} frame={frame} fps={fps} />
      ))}

      {/* ── Centred content stack ───────────────────────────────────────── */}
      <AbsoluteFill
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 28,
        }}
      >
        {/* The colour name — large, in the actual colour, white outline ensures readability */}
        <div
          style={{
            fontSize,
            fontWeight: 900,
            fontFamily,
            color: color.hex,
            // White outline keeps the text legible on any background (required for yellow)
            WebkitTextStroke: `6px white`,
            textShadow: `0 8px 24px rgba(0,0,0,0.18)`,
            transform: `scale(${finalWordScale})`,
            letterSpacing: 8,
            userSelect: 'none',
            lineHeight: 1,
          }}
        >
          {color.name.toUpperCase()}
        </div>

        {/* Colour demonstration circle — shows the actual colour */}
        <div
          style={{
            width: 120,
            height: 120,
            borderRadius: '50%',
            backgroundColor: color.hex,
            border: '8px solid white',
            boxShadow: `0 8px 32px ${color.hex}88, 0 0 0 4px ${color.blobHex}`,
            transform: `scale(${circleScale})`,
          }}
        />
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
