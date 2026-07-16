import React from 'react';
import {Composition} from 'remotion';
import {getAudioDurationInSeconds} from '@remotion/media-utils';
import {CivilWarLetter, CivilWarLetterProps} from './CivilWarLetter';
import {resolveSrc} from './resolveSrc';

const FPS = 30;

const defaultProps: CivilWarLetterProps = {
  letterText:
    'My dear colleagues,\n\n' +
    'I regret to report that I shall be unable to attend our appointed council this day. ' +
    'A most grievous rebellion has commenced within my own constitution, and I have been ' +
    'compelled to retire from the field and take refuge upon the nearest horizontal surface.\n\n' +
    'Pray proceed without me, and know that I remain, though diminished, devoted to the cause.',
  dateLine: 'Camp near the Sofa, this 30th day of June',
  signature: 'Your obedient & intestinally besieged servant, J.',
  title: 'A Letter from the Front',
  fontStyle: 'script',
  hasMusic: false,
  hasAmbient: false,
  narrationFile: 'narration.mp3',
  musicFile: 'music.mp3',
  ambientFile: 'ambient.mp3',
  ambientVolume: 0.16,
  introPad: 3.5,
  outroPad: 4,
  accentColor: '#5a2a16',
};

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="CivilWarLetter"
      component={CivilWarLetter}
      durationInFrames={60 * FPS}
      fps={FPS}
      width={1920}
      height={1080}
      defaultProps={defaultProps}
      calculateMetadata={async ({props}) => {
        // Length the video to the narration (plus the title + outro pads).
        let narration = 18;
        try {
          narration = await getAudioDurationInSeconds(resolveSrc(props.narrationFile));
        } catch (e) {
          // No narration rendered yet (e.g. in the Studio preview) — fall back.
        }
        const total = props.introPad + narration + props.outroPad;
        return {durationInFrames: Math.ceil(total * FPS), fps: FPS};
      }}
    />
  );
};
