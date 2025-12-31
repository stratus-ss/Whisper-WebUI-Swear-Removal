"""
Test swear removal functionality.
"""

import os
import sys
import pytest
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestSwearListManager:
    """Test SwearListManager functionality."""
    
    def test_load_default_list(self):
        """Test loading the default swear list."""
        from modules.swear_removal.swear_manager import SwearListManager
        
        manager = SwearListManager()
        swears_dict = manager.load_default_list()
        
        assert isinstance(swears_dict, dict)
        assert len(swears_dict) > 0
        print(f"✓ Loaded default swear list with {len(swears_dict)} words")
    
    def test_scrub_word(self):
        """Test word normalization."""
        from modules.swear_removal.swear_manager import SwearListManager
        
        # Test various normalizations
        assert SwearListManager.scrub_word("Hello!") == "hello"
        assert SwearListManager.scrub_word("WORLD?") == "world"
        assert SwearListManager.scrub_word("  test  ") == "test"
        print("✓ Word scrubbing works correctly")
    
    def test_load_json_list(self):
        """Test loading a JSON format swear list."""
        from modules.swear_removal.swear_manager import SwearListManager
        import tempfile
        
        # Create a temporary JSON file
        test_words = ["word1", "word2", "word3"]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(test_words, f)
            temp_file = f.name
        
        try:
            manager = SwearListManager()
            swears_dict = manager.load_custom_list(temp_file, "test_json")
            
            assert len(swears_dict) == 3
            assert "word1" in swears_dict
            assert "word2" in swears_dict
            assert "word3" in swears_dict
            print(f"✓ Loaded JSON swear list with {len(swears_dict)} words")
        finally:
            os.remove(temp_file)
    
    def test_load_text_list(self):
        """Test loading a text format swear list."""
        from modules.swear_removal.swear_manager import SwearListManager
        import tempfile
        
        # Create a temporary text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("word1\n")
            f.write("word2|custom_replacement\n")
            f.write("# This is a comment\n")
            f.write("word3\n")
            temp_file = f.name
        
        try:
            manager = SwearListManager()
            swears_dict = manager.load_custom_list(temp_file, "test_text")
            
            assert len(swears_dict) == 3
            assert swears_dict["word1"] == "*****"
            assert swears_dict["word2"] == "custom_replacement"
            assert "word3" in swears_dict
            print(f"✓ Loaded text swear list with {len(swears_dict)} words")
        finally:
            os.remove(temp_file)


class TestAudioCleaner:
    """Test AudioCleaner functionality."""
    
    def test_identify_censored_words(self):
        """Test identifying words to censor."""
        from modules.swear_removal.audio_cleaner import AudioCleaner
        
        word_list = [
            {'word': 'hello', 'start': 0.0, 'end': 0.5, 'conf': 0.95},
            {'word': 'damn', 'start': 0.5, 'end': 1.0, 'conf': 0.98},
            {'word': 'world', 'start': 1.0, 'end': 1.5, 'conf': 0.97},
        ]
        
        swears_dict = {'damn': '*****', 'hell': '*****'}
        
        cleaner = AudioCleaner()
        censored = cleaner.identify_censored_words(word_list, swears_dict)
        
        assert len(censored) == 1
        assert censored[0]['word'] == 'damn'
        print(f"✓ Correctly identified {len(censored)} censored word(s)")
    
    def test_save_and_load_transcript(self):
        """Test saving and loading transcripts (monkeyplug format)."""
        from modules.swear_removal.audio_cleaner import AudioCleaner
        import tempfile
        import json
        
        word_list = [
            {'word': 'hello', 'start': 0.0, 'end': 0.5, 'conf': 0.95, 'scrub': False},
            {'word': 'damn', 'start': 0.5, 'end': 1.0, 'conf': 0.98, 'scrub': True},
            {'word': 'world', 'start': 1.0, 'end': 1.5, 'conf': 0.97, 'scrub': False},
        ]
        
        # Save transcript
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            cleaner = AudioCleaner()
            cleaner._save_transcript_json(word_list, temp_file)
            
            # Verify file was created
            assert os.path.isfile(temp_file)
            print(f"✓ Transcript saved to {temp_file}")
            
            # Load transcript back
            loaded_list = cleaner.load_transcript_from_file(temp_file)
            
            assert loaded_list is not None
            assert len(loaded_list) == 3
            assert loaded_list[0]['word'] == 'hello'
            assert loaded_list[1]['scrub'] is True
            print(f"✓ Transcript loaded with {len(loaded_list)} words")
            
            # Verify format
            with open(temp_file, 'r') as f:
                data = json.load(f)
                assert isinstance(data, list)
                assert 'word' in data[0]
                assert 'start' in data[0]
                assert 'end' in data[0]
                assert 'conf' in data[0]
                assert 'scrub' in data[0]
            print("✓ Transcript format is valid (monkeyplug-compatible)")
            
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def test_create_mute_list_mute_mode(self):
        """Test creating mute list for mute mode."""
        from modules.swear_removal.audio_cleaner import AudioCleaner
        
        censored_words = [
            {'word': 'damn', 'start': 0.5, 'end': 1.0, 'conf': 0.98, 'scrub': True},
            {'word': 'hell', 'start': 2.0, 'end': 2.5, 'conf': 0.95, 'scrub': True},
        ]
        
        cleaner = AudioCleaner()
        mute_list, sine_list, beep_list = cleaner.create_mute_list(
            censored_words, 0.0, 0.0, beep=False, beep_hertz=1000
        )
        
        assert len(mute_list) > 0
        assert len(sine_list) == 0
        assert len(beep_list) == 0
        print(f"✓ Created mute list with {len(mute_list)} filters")
    
    def test_create_mute_list_beep_mode(self):
        """Test creating mute list for beep mode."""
        from modules.swear_removal.audio_cleaner import AudioCleaner
        
        censored_words = [
            {'word': 'damn', 'start': 0.5, 'end': 1.0, 'conf': 0.98, 'scrub': True},
        ]
        
        cleaner = AudioCleaner()
        mute_list, sine_list, beep_list = cleaner.create_mute_list(
            censored_words, 0.0, 0.0, beep=True, beep_hertz=1000
        )
        
        assert len(mute_list) > 0
        assert len(sine_list) > 0
        assert len(beep_list) > 0
        print(f"✓ Created beep list with {len(sine_list)} beeps")


class TestCensorshipStatistics:
    """Test CensorshipStatistics functionality."""
    
    def test_analyze_results(self):
        """Test analyzing censorship results."""
        from modules.swear_removal.statistics import CensorshipStatistics
        
        word_list = [
            {'word': 'hello', 'start': 0.0, 'end': 0.5},
            {'word': 'damn', 'start': 0.5, 'end': 1.0},
            {'word': 'world', 'start': 1.0, 'end': 1.5},
            {'word': 'hell', 'start': 1.5, 'end': 2.0},
        ]
        
        censored_words = [
            {'word': 'damn', 'start': 0.5, 'end': 1.0, 'original_word': 'damn'},
            {'word': 'hell', 'start': 1.5, 'end': 2.0, 'original_word': 'hell'},
        ]
        
        stats = CensorshipStatistics()
        analysis = stats.analyze_results(word_list, censored_words, 2.0)
        
        assert analysis['total_words'] == 4
        assert analysis['censored_count'] == 2
        assert analysis['censored_percentage'] == 50.0
        assert analysis['unique_censored_words'] == 2
        print(f"✓ Analysis: {analysis['censored_count']}/{analysis['total_words']} words censored")
    
    def test_generate_report(self):
        """Test generating a text report."""
        from modules.swear_removal.statistics import CensorshipStatistics
        
        stats = CensorshipStatistics()
        stats.total_words = 100
        stats.censored_count = 5
        
        report = stats.generate_report()
        
        assert "STATISTICS REPORT" in report
        assert "100" in report
        assert "5" in report
        print("✓ Generated report successfully")
    
    def test_generate_json_report(self):
        """Test generating a JSON report."""
        from modules.swear_removal.statistics import CensorshipStatistics
        
        stats = CensorshipStatistics()
        stats.total_words = 100
        stats.censored_count = 5
        
        json_report = stats.generate_json_report()
        
        assert 'generated_at' in json_report
        assert 'statistics' in json_report
        assert json_report['statistics']['total_words'] == 100
        print("✓ Generated JSON report successfully")


def run_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("SWEAR REMOVAL MODULE TESTS")
    print("="*60 + "\n")
    
    # Test SwearListManager
    print("Testing SwearListManager...")
    test_manager = TestSwearListManager()
    test_manager.test_load_default_list()
    test_manager.test_scrub_word()
    test_manager.test_load_json_list()
    test_manager.test_load_text_list()
    print()
    
    # Test AudioCleaner
    print("Testing AudioCleaner...")
    test_cleaner = TestAudioCleaner()
    test_cleaner.test_identify_censored_words()
    test_cleaner.test_save_and_load_transcript()
    test_cleaner.test_create_mute_list_mute_mode()
    test_cleaner.test_create_mute_list_beep_mode()
    print()
    
    # Test CensorshipStatistics
    print("Testing CensorshipStatistics...")
    test_stats = TestCensorshipStatistics()
    test_stats.test_analyze_results()
    test_stats.test_generate_report()
    test_stats.test_generate_json_report()
    print()
    
    print("="*60)
    print("ALL TESTS PASSED! ✓")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_tests()
