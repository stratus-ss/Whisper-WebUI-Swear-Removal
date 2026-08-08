import pytest

from modules.whisper.data_classes import Segment
from modules.whisper.segment_merger import SegmentMerger


def _seg(start: float, end: float, text: str, speaker: str = None) -> Segment:
    return Segment(start=start, end=end, text=text, speaker=speaker)


class TestSegmentMerger:
    """Tests for SegmentMerger.merge_segments()"""

    def test_basic_merge_lowercase_continuation(self):
        segments = [
            _seg(0.0, 1.0, "the cat sat"),
            _seg(1.2, 2.5, "on the mat"),
        ]
        result = SegmentMerger.merge_segments(segments, max_words=12, max_gap_sec=1.5)
        assert len(result) == 1
        assert result[0].text == "the cat sat on the mat"
        assert result[0].start == 0.0
        assert result[0].end == 2.5

    def test_inverted_punctuation_prevents_merge(self):
        segments = [
            _seg(0.0, 1.0, "dijo algo"),
            _seg(1.2, 3.0, "¿Cómo estás?"),
        ]
        result = SegmentMerger.merge_segments(segments, max_words=12, max_gap_sec=1.5)
        assert len(result) == 2

    def test_max_words_prevents_merge(self):
        segments = [
            _seg(0.0, 1.0, "one two three four five"),
            _seg(1.2, 2.5, "six seven eight nine ten"),
        ]
        result = SegmentMerger.merge_segments(segments, max_words=8, max_gap_sec=1.5)
        assert len(result) == 2

    def test_gap_exceeds_max_prevents_merge(self):
        segments = [
            _seg(0.0, 1.0, "hello there"),
            _seg(5.0, 6.0, "how are you"),
        ]
        result = SegmentMerger.merge_segments(segments, max_words=12, max_gap_sec=1.5)
        assert len(result) == 2

    @pytest.mark.parametrize("terminal", [".", "!", "?", "\u2026"])
    def test_terminal_punctuation_prevents_merge(self, terminal):
        segments = [
            _seg(0.0, 1.0, f"end of sentence{terminal}"),
            _seg(1.2, 2.5, "start of next"),
        ]
        result = SegmentMerger.merge_segments(segments, max_words=12, max_gap_sec=1.5)
        assert len(result) == 2

    def test_merge_across_uppercase_start(self):
        segments = [
            _seg(0.0, 1.0, "the cat sat on the mat"),
            _seg(1.2, 2.5, "She went to the store"),
        ]
        result = SegmentMerger.merge_segments(segments, max_words=20, max_gap_sec=1.5)
        assert len(result) == 1
        assert result[0].text == "the cat sat on the mat She went to the store"

    def test_multi_segment_spanish_merge(self):
        segments = [
            _seg(0.0, 0.6, "Es como"),
            _seg(0.8, 1.3, "Un cuento"),
            _seg(1.5, 2.1, "De hadas"),
        ]
        result = SegmentMerger.merge_segments(segments, max_words=12, max_gap_sec=1.5)
        assert len(result) == 1
        assert result[0].text == "Es como Un cuento De hadas"
        assert result[0].start == 0.0
        assert result[0].end == 2.1

    def test_disabled_when_max_words_zero(self):
        segments = [
            _seg(0.0, 1.0, "hello"),
            _seg(1.1, 2.0, "world"),
        ]
        result = SegmentMerger.merge_segments(segments, max_words=0, max_gap_sec=1.5)
        assert len(result) == 2
        assert result[0].text == "hello"
        assert result[1].text == "world"

    def test_same_speaker_merges_and_strips_prefix(self):
        segments = [
            _seg(0.0, 1.0, "SPEAKER_00|Hello there", speaker="SPEAKER_00"),
            _seg(1.2, 2.5, "SPEAKER_00|my friend", speaker="SPEAKER_00"),
        ]
        result = SegmentMerger.merge_segments(segments, max_words=12, max_gap_sec=1.5)
        assert len(result) == 1
        assert result[0].text == "SPEAKER_00|Hello there my friend"
        assert result[0].speaker == "SPEAKER_00"
        assert result[0].end == 2.5

    def test_different_speakers_do_not_merge(self):
        segments = [
            _seg(0.0, 1.0, "SPEAKER_00|Hello", speaker="SPEAKER_00"),
            _seg(1.2, 2.5, "SPEAKER_01|World", speaker="SPEAKER_01"),
        ]
        result = SegmentMerger.merge_segments(segments, max_words=12, max_gap_sec=1.5)
        assert len(result) == 2
        assert result[0].text == "SPEAKER_00|Hello"
        assert result[1].text == "SPEAKER_01|World"
        assert result[1].speaker == "SPEAKER_01"

    def test_none_speaker_merges_like_today(self):
        segments = [
            _seg(0.0, 1.0, "the cat sat"),
            _seg(1.2, 2.5, "on the mat"),
        ]
        result = SegmentMerger.merge_segments(segments, max_words=12, max_gap_sec=1.5)
        assert len(result) == 1
        assert result[0].text == "the cat sat on the mat"

    def test_mixed_none_and_labeled_do_not_merge(self):
        segments = [
            _seg(0.0, 1.0, "hello there"),
            _seg(1.2, 2.5, "SPEAKER_00|world", speaker="SPEAKER_00"),
        ]
        result = SegmentMerger.merge_segments(segments, max_words=12, max_gap_sec=1.5)
        assert len(result) == 2

    def test_none_prefix_stripped_on_merge(self):
        segments = [
            _seg(0.0, 1.0, "None|hello", speaker=None),
            _seg(1.2, 2.5, "None|world", speaker=None),
        ]
        result = SegmentMerger.merge_segments(segments, max_words=12, max_gap_sec=1.5)
        assert len(result) == 1
        assert result[0].text == "None|hello world"
