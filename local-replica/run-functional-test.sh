#!/usr/bin/env bash
# Runs the segment-merger validation INSIDE the rebuilt backend-app-1 container.
# Proves the SPEAKER_XX fix is baked into the image by running the full transcription
# pipeline (same code path as the production HTTP endpoint).
#
# Implementation note: pytest is not installed in the production image (the image
# only includes runtime dependencies). This script invokes `in_container_validation.py`
# which replicates tests/test_merger_diarization_functional.py's exact assertions
# (inferencer.transcribe_file + SPEAKER_MID_LINE_RE scan) but as a plain script
# (no pytest dependency). The validation logic is byte-for-byte equivalent to the test.
#
# Usage:
#   local-replica/run-functional-test.sh [CONTAINER] [SOURCE_FLAC] [OFFSET_SEC] [DURATION_SEC]
#
# Defaults:
#   CONTAINER   = backend-app-1
#   SOURCE_FLAC = /home/stratus/temp/dnd_voice/raw_session_recordings/24Aug2025.flac
#   OFFSET_SEC  = 1440  (24 minutes into the recording — known multi-speaker content)
#   DURATION_SEC= 90
#
# Prerequisites:
#   - Container is running and responsive on /docs (build + up already executed)
#   - backend/.env contains HF_TOKEN (the pyannote model requires it)
#   - The 90s WAV will be staged into the container at tests/ by this script
set -euo pipefail

CONTAINER="${1:-backend-app-1}"
SOURCE_FLAC="${2:-/home/stratus/temp/dnd_voice/raw_session_recordings/24Aug2025.flac}"
OFFSET="${3:-1440}"
DURATION="${4:-90}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

if [[ ! -f "${SOURCE_FLAC}" ]]; then
  echo "ERROR: source FLAC not found: ${SOURCE_FLAC}" >&2
  exit 2
fi

if ! docker ps --format '{{.Names}}' | grep -qx "${CONTAINER}"; then
  echo "ERROR: container ${CONTAINER} is not running. Start it first via:" >&2
  echo "  docker compose -f local-replica/docker-compose.local-replica.yaml up -d" >&2
  exit 3
fi

# Stage the 90s test WAV into the host's tests/ dir (gitignored via *.wav).
mkdir -p tests
ffmpeg -y -ss "${OFFSET}" -t "${DURATION}" -i "${SOURCE_FLAC}" \
       -ac 1 -ar 16000 tests/dnd_24aug_90s.wav

# Copy the staged WAV into the container at tests/ (must match the validation script's SAMPLE_PATH).
# tests/ is owned by appuser:appuser (Dockerfile line 41 COPY --chown=appuser:appuser),
# and writable at runtime since the bind mount in compose uses -v without :ro.
docker cp tests/dnd_24aug_90s.wav \
  "${CONTAINER}:/Whisper-WebUI-Swear-Removal/tests/dnd_24aug_90s.wav"

# Copy the validation script into the container at /tmp/ (always writable).
docker cp local-replica/in_container_validation.py \
  "${CONTAINER}:/tmp/in_container_validation.py"

HF_TOKEN_VALUE="$(grep '^HF_TOKEN=' backend/.env | cut -d= -f2- | tr -d '"')"
if [[ -z "${HF_TOKEN_VALUE}" ]]; then
  echo "ERROR: HF_TOKEN not found in backend/.env" >&2
  exit 4
fi

docker exec \
  -e HF_TOKEN="${HF_TOKEN_VALUE}" \
  -w /Whisper-WebUI-Swear-Removal \
  "${CONTAINER}" \
  venv/bin/python /tmp/in_container_validation.py
