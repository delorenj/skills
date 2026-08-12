import {Config} from '@remotion/cli/config';

Config.setVideoImageFormat('jpeg');
Config.setJpegQuality(95);
Config.setOverwriteOutput(true);
Config.setCodec('h264');
// Keep the 1920x1080 design canvas while emitting a lightweight 1280x720
// delivery file. At 60fps this has a similar pixel budget to the former
// 1080p30 render, but eliminates the cadence judder and stays below the depot's
// 100MB upload ceiling for normal dispatches.
Config.setScale(2 / 3);
Config.setCrf(22);
Config.setX264Preset('medium');
Config.setGopSize(120);
Config.setPixelFormat('yuv420p');
Config.setColorSpace('bt709');
