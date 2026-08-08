"""Standalone validation that replicates tests/test_merger_diarization_functional.py.

Runs the same pipeline code path that pytest would run, but as a plain script
(no pytest dependency in the production image). Invoked via:

    docker exec <container> venv/bin/python /tmp/in_container_validation.py

The script:
1. Builds a FasterWhisperInference pipeline (WhisperFactory.create_whisper_inference)
2. Runs transcribe_file with merge_max_words=12 (production default)
3. Reads the SRT output and asserts no mid-line SPEAKER_XX labels

Exits 0 on PASS, 1 on FAIL.
"""
import os
import re
import sys

import gradio as gr

from modules.whisper.whisper_factory import WhisperFactory
from modules.whisper.data_classes import (
    TranscriptionPipelineParams, WhisperParams, VadParams,
    BGMSeparationParams, DiarizationParams,
)
from modules.utils.paths import WEBUI_DIR

SAMPLE_PATH = os.path.join(WEBUI_DIR, "tests", "dnd_24aug_90s.wav")
SPEAKER_MID_LINE_RE = re.compile(r"\bSPEAKER_\d+\|")


def main() -> int:
    if not os.path.exists(SAMPLE_PATH):
        print(f"FAIL: staged sample missing at {SAMPLE_PATH}", file=sys.stderr)
        return 1

    hparams = TranscriptionPipelineParams(
        whisper=WhisperParams(model_size="small", compute_type="float16", merge_max_words=12),
        vad=VadParams(vad_filter=False),
        bgm_separation=BGMSeparationParams(is_separate_bgm=False),
        diarization=DiarizationParams(is_diarize=True),
    ).to_list()

    print("Loading FasterWhisperInference pipeline (small model + pyannote diarization)...")
    inferencer = WhisperFactory.create_whisper_inference("faster-whisper")
    print("Running transcribe_file() on 90s multi-speaker audio...")
    subtitle_str, _ = inferencer.transcribe_file(
        [SAMPLE_PATH], None, None, None, "SRT", False, gr.Progress(),
        *hparams,
    )

    lines = [l.strip() for l in subtitle_str.splitlines() if l.strip()]
    speaker_lines = [l for l in lines if SPEAKER_MID_LINE_RE.match(l)]
    if not speaker_lines:
        print("FAIL: no speaker-labeled lines found — diarization did not run?", file=sys.stderr)
        return 1

    matched = SPEAKER_MID_LINE_RE.match(speaker_lines[0])
    offenders = [
        (i, l) for i, l in enumerate(speaker_lines)
        if SPEAKER_MID_LINE_RE.search(l, matched.end())
    ]
    if offenders:
        print(f"FAIL: mid-line SPEAKER_XX labels found: {offenders}", file=sys.stderr)
        return 1

    print(f"PASS: {len(speaker_lines)} speaker-labeled lines, 0 mid-line SPEAKER_XX labels")
    return 0


if __name__ == "__main__":
    sys.exit(main())
