import React from 'react';
import {AbsoluteFill, spring, useCurrentFrame, useVideoConfig, random} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Nunito';
import {ColorDef} from './LearnColors';
import {MusicNote} from './components/MusicNote';
import {Star} from './components/Star';
import {Sparkle} from './components/Sparkle';
import {Watermark} from './Watermark';

// Load Nunito Black — rounded, friendly, great for kids content.
// Called at module level so Remotion blocks rendering until the font is ready.
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

  // ── Title entrance spring ──────────────────────────────────────────────────
  // TransitionSeries handles fade in/out at scene edges — no manual opacity needed.
  const titleScale = spring({
    frame,
    fps,
    config: {damping: 8}, // bouncy entrance, per skill best practices
    durationInFrames: 40,
  });

  // Gentle continuous bounce once the spring has settled (~40 frames)
  const continuousBounce =
    frame > 40
      ? Math.sin((frame / fps) * Math.PI * 1.6) * 0.04 + 1
      : 1;

  const finalScale = titleScale * continuousBounce;

  // ── Swatch circle entrance — slightly delayed ──────────────────────────────
  const swatchScale = spring({
    frame,
    fps,
    config: {damping: 8},
    durationInFrames: 35,
    delay: 8,
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

  // ── Rising sparkle confetti dots (10 dots) ────────────────────────────────
  const sparkles = Array.from({length: 10}, (_, i) => ({
    x: random(`sparkle-x-${sceneIndex}-${i}`) * width,
    startY: height + 20,
    size: random(`sparkle-size-${sceneIndex}-${i}`) * 14 + 8,
    speed: random(`sparkle-speed-${sceneIndex}-${i}`) * 0.6 + 0.3,
    phase: random(`sparkle-phase-${sceneIndex}-${i}`) * Math.PI * 2,
    hue: random(`sparkle-hue-${sceneIndex}-${i}`) * 360,
  }));

  return (
    <AbsoluteFill>
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
        {/* Color name */}
        <div
          style={{
            fontSize: 148,
            fontWeight: 900,
            fontFamily,
            color: color.textColor,
            textShadow: [
              '0 6px 0 rgba(0,0,0,0.22)',
              '0 12px 24px rgba(0,0,0,0.18)',
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
            boxShadow: `0 8px 30px rgba(0,0,0,0.22), 0 0 0 4px ${color.bg}`,
            transform: `scale(${swatchScale})`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
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
