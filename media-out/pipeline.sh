#!/usr/bin/env bash
# Video pipeline: render -> mix -> [Resolve polish] -> Postiz upload.
#
#   ./pipeline.sh                 render.js + ffmpeg auto-mix (headless; Hulk or M4)
#   ./pipeline.sh --resolve       also build the Resolve timeline for manual polish (M4, Studio)
#   ./pipeline.sh --skip-render   reuse the existing silent MP4
#   ./pipeline.sh --upload-only   upload media-out/<NAME>_FINAL.mp4 as-is (e.g. after a Resolve export)
#   ./pipeline.sh --upload        push the final MP4 to Postiz (needs POSTIZ_API_KEY; POSTIZ_URL optional)
#
# The ffmpeg mix ducks the music (A2) under the voice (A1) automatically, so a postable
# file exists without opening Resolve. Use --resolve only when you want SFX/hand edits.
set -euo pipefail
cd "$(dirname "$0")"

NAME=${NAME:-kidney_not_done_yet}
SILENT=${NAME}_9x16.mp4 VO=${VO:-kidney_vo.wav} MUSIC=${MUSIC:-kidney_music_bed.wav}
FINAL=${NAME}_FINAL.mp4
RENDER=1 MIX=1 RESOLVE=0 UPLOAD=0
for a in "$@"; do case $a in
  --skip-render) RENDER=0 ;; --resolve) RESOLVE=1 ;; --upload) UPLOAD=1 ;;
  --upload-only) RENDER=0 MIX=0 UPLOAD=1 ;;
  *) echo "unknown flag: $a" >&2; exit 2 ;; esac; done

if [ $RENDER = 1 ]; then node render.js; fi

if [ $MIX = 1 ]; then
# Voice at full level, music -20 dB and sidechain-ducked under the voice, loudness-normalised for social.
ffmpeg -y -loglevel error -i "$SILENT" -i "$VO" -i "$MUSIC" -filter_complex \
  "[2:a]volume=-20dB[m];[1:a]asplit[v1][v2];[m][v2]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[d];\
[v1][d]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$FINAL"
echo "Mixed -> media-out/$FINAL"
fi

if [ $RESOLVE = 1 ]; then
  export RESOLVE_SCRIPT_API="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
  export RESOLVE_SCRIPT_LIB="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
  export PYTHONPATH="${PYTHONPATH:-}:$RESOLVE_SCRIPT_API/Modules/"
  python3 resolve_build.py
  echo "Polish in Resolve, Deliver to media-out/$FINAL (overwrite), then: $0 --upload-only"
fi

if [ $UPLOAD = 1 ]; then
  : "${POSTIZ_API_KEY:?set POSTIZ_API_KEY}"
  curl -sSf -H "Authorization: Bearer $POSTIZ_API_KEY" -F "file=@$FINAL" \
    "${POSTIZ_URL:-https://api.postiz.com}/public/v1/upload"
  echo; echo "Use the returned url in posts:create (see SKILL.md)."
fi
