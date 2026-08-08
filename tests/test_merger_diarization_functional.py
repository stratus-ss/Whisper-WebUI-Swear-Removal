"""GPU functional test: real diarization + segment merger on multi-speaker audio.

Regression: merged lines must never contain a mid-line SPEAKER_XX label.
"""
import os
import re
import pytest
import gradio as gr

from modules.whisper.whisper_factory import WhisperFactory
from modules.whisper.data_classes import (
    TranscriptionPipelineParams, WhisperParams, VadParams,
    BGMSeparationParams, DiarizationParams,
)
from modules.utils.paths import WEBUI_DIR
from modules.utils.subtitle_manager import read_file

SAMPLE_PATH = os.path.join(WEBUI_DIR, "tests", "dnd_24aug_90s.wav")
SPEAKER_MID_LINE_RE = re.compile(r'\bSPEAKER_\d+\|')


def _hparams(merge_max_words: int):
    return TranscriptionPipelineParams(
        whisper=WhisperParams(model_size="small", compute_type="float16", merge_max_words=merge_max_words),
        vad=VadParams(vad_filter=False),
        bgm_separation=BGMSeparationParams(is_separate_bgm=False),
        diarization=DiarizationParams(is_diarize=True),
    ).to_list()


@pytest.mark.skipif(not os.path.exists(SAMPLE_PATH), reason="staged sample missing")
def test_no_mid_line_speaker_labels_with_merging():
    inferencer = WhisperFactory.create_whisper_inference("faster-whisper")
    subtitle_str, _ = inferencer.transcribe_file(
        [SAMPLE_PATH], None, None, None, "SRT", False, gr.Progress(),
        *_hparams(merge_max_words=12),
    )
    lines = [l.strip() for l in subtitle_str.splitlines() if l.strip()]
    speaker_lines = [l for l in lines if SPEAKER_MID_LINE_RE.match(l)]
    assert speaker_lines, "no speaker-labeled lines found (diarization did not run?)"
    offenders = [
        (i, l) for i, l in enumerate(speaker_lines)
        if SPEAKER_MID_LINE_RE.search(l, SPEAKER_MID_LINE_RE.match(l).end())
    ]
    assert not offenders, f"mid-line SPEAKER_XX labels found: {offenders}"
