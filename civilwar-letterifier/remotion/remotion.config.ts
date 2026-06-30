import {Config} from '@remotion/cli/config';

Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);
// Audio is mixed automatically; ensure good quality.
Config.setCodec('h264');
