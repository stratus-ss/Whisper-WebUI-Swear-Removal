#!/usr/bin/env bash
# extract_audio.sh — Convert video files to MP3 tuned for STT ingestion.
#
# Defaults match the STT server's expectations: mono 16 kHz MP3
# (~140 kbps VBR). MP3s land beside the source video by default.
#
# Usage:
#   extract_audio.sh                      # convert everything in PWD
#   extract_audio.sh --watch DIR          # tail-style watch on DIR (inotifywait)
#   extract_audio.sh FILE [FILE ...]      # convert specific files
#   extract_audio.sh --dest DIR FILE ...  # write MP3s into DIR
#   extract_audio.sh --parallel N DIR     # override parallel jobs (default: nproc/2)
#
# Requires: ffmpeg, GNU xargs (or inotifywait if --watch).

set -euo pipefail

DEST=""
PARALLEL=""
WATCH_DIR=""
LOG_PREFIX="extract_audio"

usage() {
  sed -n '2,12p' "$0"
  exit "${1:-0}"
}

# Simple arg loop — keep it bash-only, no getopts dependency weirdness.
TARGETS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)      usage 0 ;;
    --dest)         DEST="$2"; shift 2 ;;
    --parallel|-P)  PARALLEL="$2"; shift 2 ;;
    --watch)        WATCH_DIR="$2"; shift 2 ;;
    --log-prefix)   LOG_PREFIX="$2"; shift 2 ;;
    -*)             echo "Unknown flag: $1" >&2; usage 1 ;;
    *)              TARGETS+=("$1"); shift ;;
  esac
done

if [[ -n "$WATCH_DIR" ]]; then
  command -v inotifywait >/dev/null || { echo "inotifywait not found (install inotify-tools)" >&2; exit 1; }
  WATCH_DIR="$(realpath "$WATCH_DIR")"
  mkdir -p "$WATCH_DIR"
  echo "[$LOG_PREFIX] watching $WATCH_DIR for new mkv/mp4/avi"
  inotifywait -m -q --format '%f' -e close_write,moved_to "$WATCH_DIR" \
    | grep --line-buffered -Ei '\.(mkv|mp4|avi)$' \
    | while read -r f; do
        sleep 1   # let the writer finish renaming
        [[ -f "$WATCH_DIR/$f" ]] && extract_one "$WATCH_DIR/$f"
      done
  exit 0
fi

if [[ ${#TARGETS[@]} -eq 0 ]]; then
  TARGETS=(".")
fi

# Collect inputs into a temp list for xargs.
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

for t in "${TARGETS[@]}"; do
  if [[ -d "$t" ]]; then
    find "$t" -maxdepth 1 -type f \( -name '*.mkv' -o -name '*.mp4' -o -name '*.avi' \) >> "$TMP"
  else
    echo "$t" >> "$TMP"
  fi
done

# Realpath everything so xargs sees absolute paths (in case cwd was used).
sort -u "$TMP" -o "$TMP"

if [[ ! -s "$TMP" ]]; then
  echo "[$LOG_PREFIX] no video files found"
  exit 0
fi

# Default parallelism: half the cores (rounded down, min 1).
if [[ -z "$PARALLEL" ]]; then
  if command -v nproc >/dev/null; then
    PARALLEL=$(awk -v n=$(nproc) 'BEGIN { p=int(n/2); if (p<1) p=1; print p }')
  else
    PARALLEL=2
  fi
fi

echo "[$LOG_PREFIX] $(wc -l < "$TMP") file(s), parallel=$PARALLEL, dest=${DEST:-<alongside input>}"

extract_one() {
  local in="$1"
  local out
  local stem="${in%.*}"

  if [[ -n "$DEST" ]]; then
    mkdir -p "$DEST"
    out="$DEST/$(basename "$stem").mp3"
  else
    out="${stem}.mp3"
  fi

  if [[ -f "$out" ]]; then
    echo "[skip] $out already exists"
    return 0
  fi

  echo "[encode] $(basename "$in")  ->  $(basename "$out")"
  if ffmpeg -nostdin -hide_banner -loglevel error \
       -i "$in" -vn -ac 1 -ar 16000 -c:a libmp3lame -q:a 4 "$out"; then
    echo "[ok] $(basename "$out")"
  else
    echo "[fail] $(basename "$in")" >&2
    rm -f "$out"  # don't leave a partial mp3
    return 1
  fi
}

export -f extract_one
export DEST LOG_PREFIX

xargs -d '\n' -I{} -P "$PARALLEL" bash -c 'extract_one "$@"' _ {} < "$TMP"

echo "[$LOG_PREFIX] done"
