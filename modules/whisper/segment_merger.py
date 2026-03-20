import re
from typing import List

from modules.whisper.data_classes import Segment


SENTENCE_TERMINALS = re.compile(r'[.!?…]\s*$')
INVERTED_PUNCT = re.compile(r'^[¡¿]')


class SegmentMerger:
    """Post-processes Whisper segments by merging short, consecutive blocks
    into longer subtitle lines based on timing, word-count, and punctuation
    heuristics that work across English, German, and Spanish."""

    @staticmethod
    def _word_count(text: str) -> int:
        return len(text.split())

    @staticmethod
    def _should_merge(current_text: str, next_text: str,
                      gap: float, combined_words: int,
                      max_words: int, max_gap_sec: float) -> bool:
        if combined_words > max_words:
            return False
        if gap > max_gap_sec:
            return False
        if SENTENCE_TERMINALS.search(current_text):
            return False
        if INVERTED_PUNCT.match(next_text):
            return False
        return True

    @staticmethod
    def merge_segments(segments: List[Segment],
                       max_words: int = 12,
                       max_gap_sec: float = 1.5) -> List[Segment]:
        """Merge consecutive subtitle segments that belong to the same phrase.

        Returns the original list unmodified when *max_words* is 0 (disabled).
        """
        if max_words <= 0 or not segments:
            return segments

        merged: List[Segment] = []
        current = segments[0].model_copy()

        for next_seg in segments[1:]:
            cur_text = (current.text or "").strip()
            nxt_text = (next_seg.text or "").strip()

            if not cur_text:
                merged.append(current)
                current = next_seg.model_copy()
                continue

            if not nxt_text:
                merged.append(current)
                current = next_seg.model_copy()
                continue

            gap = (next_seg.start or 0.0) - (current.end or 0.0)
            combined_words = (
                SegmentMerger._word_count(cur_text)
                + SegmentMerger._word_count(nxt_text)
            )

            if SegmentMerger._should_merge(
                cur_text, nxt_text, gap, combined_words,
                max_words, max_gap_sec
            ):
                current.text = f"{cur_text} {nxt_text}"
                current.end = next_seg.end
                if current.words is not None and next_seg.words is not None:
                    current.words = list(current.words) + list(next_seg.words)
            else:
                merged.append(current)
                current = next_seg.model_copy()

        merged.append(current)
        return merged
