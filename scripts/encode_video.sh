#!/usr/bin/env bash
set -euo pipefail

usage() {
cat <<'USAGE'
encode_video.sh IN OUT [MAXWIDTH] [CRF] [POSTER_TIME]

Re-encode a clip (MP4, M4V, MOV, or animated GIF) for the web:
H.264, yuv420p, faststart, no audio, width capped at MAXWIDTH
(default 1280), CRF default 26, preset slow. Writes OUT and a
poster frame OUT_poster.jpg (taken at POSTER_TIME, default
00:00:01, or "last" for the final frame).

Target is under 6 MB per clip. If a clip is larger, rerun with a
higher CRF or MAXWIDTH 960, then check a frame to make sure any
text in the animation is still legible.

Example:
  scripts/encode_video.sh ~/Dropbox/Visuals/tess_sky.mp4 video/tess_sky.mp4
  scripts/encode_video.sh img/Na_HIPc.gif video/Na_HIPc.mp4 960 28
USAGE
}

if [ $# -lt 2 ]; then
  usage
  exit 1
fi

IN="$1"
OUT="$2"
MAXW="${3:-1280}"
CRF="${4:-26}"
PT="${5:-00:00:01}"
POSTER="${OUT%.*}_poster.jpg"
TMP="$(mktemp -t encvid).mp4"

ffmpeg -y -loglevel error -i "$IN" \
  -vf "scale='min(${MAXW},iw)':-2:flags=lanczos,format=yuv420p" \
  -c:v libx264 -crf "$CRF" -preset slow -pix_fmt yuv420p \
  -movflags +faststart -an "$TMP"
mv "$TMP" "$OUT"

if [ "$PT" = "last" ]; then
  ffmpeg -y -loglevel error -sseof -0.2 -i "$OUT" -update 1 -frames:v 1 -q:v 3 "$POSTER"
else
  ffmpeg -y -loglevel error -ss "$PT" -i "$OUT" -frames:v 1 -q:v 3 "$POSTER"
fi

SIZE=$(stat -f%z "$OUT" 2>/dev/null || stat -c%s "$OUT")
echo "$OUT: $((SIZE / 1024)) KB, poster $POSTER"
if [ "$SIZE" -gt 6291456 ]; then
  echo "WARNING: $OUT is over 6 MB" >&2
fi
