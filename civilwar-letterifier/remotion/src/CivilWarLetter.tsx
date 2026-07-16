import React, {useLayoutEffect, useRef, useState} from 'react';
import {
  AbsoluteFill,
  Audio,
  Easing,
  Sequence,
  continueRender,
  delayRender,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {loadFont as loadScript} from '@remotion/google-fonts/Tangerine';
import {loadFont as loadDispatch} from '@remotion/google-fonts/IMFellEnglish';
import {resolveSrc} from './resolveSrc';

// Two period-appropriate looks:
//  - "script"   -> Tangerine: an elegant 19th-century calligraphic hand (the default "fancy script")
//  - "dispatch" -> IM Fell English: a historically faithful printed-dispatch typeface
const {fontFamily: scriptFamily} = loadScript();
const {fontFamily: dispatchFamily} = loadDispatch();

export type CivilWarLetterProps = {
  /** The full letter body. Use \n for line breaks; blank lines separate paragraphs. */
  letterText: string;
  /** Small line above the letter, e.g. "Camp near Antietam, September 1862". */
  dateLine: string;
  /** Closing signature, rendered larger in script. */
  signature: string;
  /** Title-card text shown during the opening pad. */
  title: string;
  /** "script" (Tangerine, default) or "dispatch" (IM Fell English). */
  fontStyle: 'script' | 'dispatch';
  /** Whether a music bed exists at public/music.mp3. */
  hasMusic: boolean;
  /** Whether an ambient bed exists at public/ambient.mp3 (layered independent of music). */
  hasAmbient: boolean;
  /** Narration audio file in public/. */
  narrationFile: string;
  /** Music bed file in public/. */
  musicFile: string;
  /** Ambient bed file in public/. */
  ambientFile: string;
  /** Peak volume of the ambient bed (0..1); it plays for the whole film. */
  ambientVolume: number;
  /** Seconds of silent title card before narration begins. */
  introPad: number;
  /** Seconds of held image / fade-out after narration ends. */
  outroPad: number;
  /** Accent ink color for the date line and signature. */
  accentColor: string;
};

const INK = '#2b1a0c';

export const CivilWarLetter: React.FC<CivilWarLetterProps> = ({
  letterText,
  dateLine,
  signature,
  title,
  fontStyle,
  hasMusic,
  hasAmbient,
  narrationFile,
  musicFile,
  ambientFile,
  ambientVolume,
  introPad,
  outroPad,
  accentColor,
}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames, width, height} = useVideoConfig();

  const bodyFamily = fontStyle === 'dispatch' ? dispatchFamily : scriptFamily;
  const isScript = fontStyle !== 'dispatch';

  // --- Measure the rendered letter so the Ken Burns pan ends exactly on the
  //     final line, regardless of how the text wraps. delayRender keeps every
  //     frame waiting until the measurement is in. ---
  const letterRef = useRef<HTMLDivElement>(null);
  const [contentHeight, setContentHeight] = useState<number>(height);
  const [handle] = useState(() => delayRender('measure-letter'));

  useLayoutEffect(() => {
    let cancelled = false;
    const measure = () => {
      if (!cancelled && letterRef.current) {
        setContentHeight(letterRef.current.scrollHeight);
      }
      if (!cancelled) continueRender(handle);
    };
    // Wait for the script/dispatch webfonts so the measured height is correct,
    // otherwise the Ken Burns pan can over- or under-shoot the final line.
    // The .catch is essential: if a font fails to load, we still measure and
    // resolve the delayRender handle, so the render never hangs to timeout.
    const fonts = typeof document !== 'undefined' ? document.fonts : undefined;
    if (fonts && fonts.ready) {
      fonts.ready.then(measure).catch(measure);
    } else {
      measure();
    }
    return () => {
      cancelled = true;
    };
  }, [handle, letterText, bodyFamily]);

  // Narration spans the window between the intro and outro pads.
  const introFrames = Math.round(introPad * fps);
  const outroFrames = Math.round(outroPad * fps);
  const readStart = introFrames;
  const readEnd = durationInFrames - outroFrames;
  const progress = interpolate(frame, [readStart, readEnd], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const eased = Easing.inOut(Easing.ease)(progress);

  // --- Ken Burns drift: slow continuous zoom + a downward pan that tracks the
  //     reading, so the camera glides down the page like the documentaries. ---
  const topMargin = height * 0.14; // where the first lines sit
  const bottomMargin = height * 0.14;
  const overflow = contentHeight - (height - topMargin - bottomMargin);
  // Only pan when the letter is taller than the frame; short letters just drift.
  const panDistance = Math.max(0, overflow);
  const translateY = topMargin - eased * panDistance;
  const scale = interpolate(eased, [0, 1], [1.03, 1.12]);

  // --- Candlelight flicker: a few detuned sines so it never looks periodic. ---
  const flicker =
    0.78 +
    0.07 * Math.sin(frame * 0.55) +
    0.05 * Math.sin(frame * 1.7 + 1.1) +
    0.035 * Math.sin(frame * 3.3 + 2.2);

  // Opening title + closing fades.
  const titleOpacity = interpolate(
    frame,
    [0, fps * 0.6, introFrames - fps * 0.5, introFrames],
    [0, 1, 1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );
  const letterFadeIn = interpolate(frame, [introFrames, introFrames + fps * 0.8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const outroFade = interpolate(
    frame,
    [durationInFrames - outroFrames + fps * 0.4, durationInFrames - fps * 0.2],
    [0, 1],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );

  const letterColumnWidth = Math.min(width * 0.62, 1180);

  return (
    <AbsoluteFill style={{backgroundColor: '#0b0805'}}>
      {/* Whole-scene archival color grade */}
      <AbsoluteFill
        style={{
          filter: 'sepia(0.35) contrast(1.05) brightness(1.02) saturate(0.92)',
        }}
      >
        {/* Aged parchment base */}
        <AbsoluteFill
          style={{
            background:
              'radial-gradient(ellipse at 50% 42%, #f4e8c9 0%, #ecdcb0 48%, #dcc488 78%, #cbae6e 100%)',
          }}
        />
        {/* Paper grain (fractal noise, multiplied onto the parchment) */}
        <AbsoluteFill style={{opacity: 0.5, mixBlendMode: 'multiply'}}>
          <svg width="100%" height="100%">
            <filter id="paper">
              <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="7" />
              <feColorMatrix type="saturate" values="0" />
            </filter>
            <rect width="100%" height="100%" filter="url(#paper)" opacity="0.25" />
          </svg>
        </AbsoluteFill>

        {/* The letter, drifting under the camera */}
        <AbsoluteFill
          style={{
            opacity: letterFadeIn,
            transform: `scale(${scale})`,
            transformOrigin: '50% 38%',
          }}
        >
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: '50%',
              width: letterColumnWidth,
              transform: `translate(-50%, ${translateY}px)`,
            }}
          >
            <div ref={letterRef}>
              <div
                style={{
                  fontFamily: dispatchFamily,
                  fontStyle: 'italic',
                  fontSize: 34,
                  color: accentColor,
                  letterSpacing: 1,
                  marginBottom: 36,
                  textAlign: 'right',
                  opacity: 0.85,
                }}
              >
                {dateLine}
              </div>

              <div
                style={{
                  fontFamily: bodyFamily,
                  fontSize: isScript ? 76 : 46,
                  lineHeight: isScript ? 1.18 : 1.6,
                  color: INK,
                  whiteSpace: 'pre-wrap',
                  textShadow: '0 1px 0 rgba(43,26,12,0.12)',
                }}
              >
                {letterText}
              </div>

              {/* Legacy standalone signature. The letterified note now carries
                  its own cohesive sign-off inside letterText, so build.mjs passes
                  an empty string and this renders nothing. Kept for back-compat
                  with any caller that still supplies a separate signature. */}
              {signature ? (
                <div
                  style={{
                    fontFamily: scriptFamily,
                    fontSize: 92,
                    color: accentColor,
                    marginTop: 40,
                    paddingLeft: '8%',
                  }}
                >
                  {signature}
                </div>
              ) : null}
            </div>
          </div>
        </AbsoluteFill>

        {/* Warm candlelight glow, flickering */}
        <AbsoluteFill
          style={{
            background:
              'radial-gradient(circle at 28% 22%, rgba(255,196,112,0.45) 0%, rgba(255,170,70,0.12) 30%, rgba(0,0,0,0) 60%)',
            mixBlendMode: 'soft-light',
            opacity: flicker,
          }}
        />
      </AbsoluteFill>

      {/* Burnt-edge vignette (outside the grade so the darkness stays deep) */}
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(ellipse at 50% 46%, rgba(0,0,0,0) 52%, rgba(46,24,6,0.45) 82%, rgba(20,10,2,0.78) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* Opening title card */}
      <AbsoluteFill
        style={{
          justifyContent: 'center',
          alignItems: 'center',
          opacity: titleOpacity,
        }}
      >
        <div
          style={{
            fontFamily: dispatchFamily,
            fontSize: 78,
            color: '#f3e4c0',
            textAlign: 'center',
            letterSpacing: 3,
            textShadow: '0 4px 24px rgba(0,0,0,0.8)',
            padding: '0 12%',
          }}
        >
          {title}
        </div>
      </AbsoluteFill>

      {/* Outro fade to black */}
      <AbsoluteFill style={{backgroundColor: '#000', opacity: outroFade}} />

      {/* Ambient bed: the always-on field atmosphere (crickets, wind, distant
          camp). Plays beneath everything for the whole film — independent of the
          optional music bed — looped, ducked low, fading in at the open and out
          under the closing fade-to-black. */}
      {hasAmbient ? (
        <Audio
          src={resolveSrc(ambientFile)}
          loop
          loopVolumeCurveBehavior="extend"
          volume={(f) =>
            interpolate(
              f,
              [0, fps * 2, durationInFrames - fps * 2.5, durationInFrames],
              [0, ambientVolume, ambientVolume, 0],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
            )
          }
        />
      ) : null}

      {/* Narration begins after the title card */}
      <Sequence from={readStart}>
        <Audio src={resolveSrc(narrationFile)} />
      </Sequence>

      {/* Music bed: looped, ducked under the voice, fading in and out */}
      {hasMusic ? (
        <Audio
          src={resolveSrc(musicFile)}
          loop
          // "extend" keeps the frame counter running across loops, so the
          // fade-in / fade-out below (keyed to absolute composition frames)
          // works instead of resetting to 0 on every repeat.
          loopVolumeCurveBehavior="extend"
          volume={(f) =>
            interpolate(
              f,
              [0, fps * 1.5, durationInFrames - fps * 2.5, durationInFrames],
              [0, 0.22, 0.22, 0],
              {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
            )
          }
        />
      ) : null}
    </AbsoluteFill>
  );
};
