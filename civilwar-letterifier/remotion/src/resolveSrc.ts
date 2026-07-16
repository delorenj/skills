import {staticFile} from 'remotion';

/**
 * Resolve an audio (or other asset) source that may be either:
 *  - a bare filename living in the local `public/` folder — the
 *    dev / Remotion Studio convenience — resolved via `staticFile()`, or
 *  - a full `http(s)://` URL — used at Lambda render time, passed in via
 *    `inputProps` — used as-is.
 *
 * Remotion Lambda bundles the site once at deploy time, so a per-render
 * file (e.g. a freshly generated narration.mp3) written to the local
 * `public/` dir never reaches the cloud render. Passing a URL instead lets
 * Lambda fetch the file directly at render time.
 */
export const resolveSrc = (f: string): string =>
  /^https?:\/\//.test(f) ? f : staticFile(f);
