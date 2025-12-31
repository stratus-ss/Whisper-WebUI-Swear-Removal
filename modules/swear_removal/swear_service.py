import os
import json
from typing import Dict, List, Tuple, Callable

from modules.swear_removal.swear_manager import SwearListManager
from modules.swear_removal.audio_cleaner import AudioCleaner
from modules.swear_removal.statistics import CensorshipStatistics
from modules.swear_removal.transcript_cache import TranscriptCache
from modules.utils.paths import (
    SWEAR_REMOVAL_AUDIO_OUTPUT_DIR,
    SWEAR_REMOVAL_TRANSCRIPT_OUTPUT_DIR,
    SWEAR_REMOVAL_STATISTICS_OUTPUT_DIR
)
from modules.utils.logger import get_logger

logger = get_logger()


class SwearRemovalService:
    """Shared service for swear removal operations."""
    
    def __init__(self, transcript_cache_dir: str = SWEAR_REMOVAL_TRANSCRIPT_OUTPUT_DIR):
        self.swear_manager = SwearListManager()
        self.audio_cleaner = AudioCleaner()
        self.stats_generator = CensorshipStatistics()
        self.transcript_cache = TranscriptCache(transcript_cache_dir)
    
    def get_or_create_transcript(
        self, 
        audio_path: str, 
        base_name: str,
        transcribe_fn: Callable[[], List[Dict]],
        reuse: bool = True
    ) -> Tuple[List[Dict], bool]:
        """
        Get transcript from cache or create new one.
        
        Args:
            audio_path: Path to audio file
            base_name: Base name of file
            transcribe_fn: Function to call for transcription
            reuse: Whether to reuse cached transcript
            
        Returns:
            Tuple of (word_list, was_cached)
        """
        if not reuse:
            word_list = transcribe_fn()
            return word_list, False
        
        # Try to load from cache
        transcript_path = self.transcript_cache.find_transcript(audio_path, base_name)
        
        if transcript_path:
            word_list = self.transcript_cache.load_transcript_file(transcript_path)
            if word_list:
                logger.info(f"Reusing cached transcript with {len(word_list)} words")
                return word_list, True
        
        # Not in cache, transcribe
        word_list = transcribe_fn()
        return word_list, False
    
    def get_output_filename(
        self, 
        base_name: str, 
        timestamp: str, 
        output_format: str, 
        input_path: str
    ) -> str:
        """
        Generate output filename based on format.
        
        Args:
            base_name: Base name of file
            timestamp: Timestamp string
            output_format: Desired output format or "MATCH"
            input_path: Original input file path
            
        Returns:
            Output filename with extension
        """
        if output_format.upper() == "MATCH":
            ext = os.path.splitext(input_path)[1].lstrip('.')
            return f"{base_name}_clean_{timestamp}.{ext}"
        return f"{base_name}_clean_{timestamp}.{output_format.lower()}"
    
    def save_statistics_files(
        self,
        base_name: str,
        timestamp: str,
        word_list: List[Dict],
        censored_words: List[Dict],
        analysis: Dict,
        transcript_loaded: bool = False
    ) -> Tuple[str, str]:
        """
        Save transcript and statistics files.
        
        Args:
            base_name: Base name of file
            timestamp: Timestamp string
            word_list: List of all words
            censored_words: List of censored words
            analysis: Statistics analysis
            transcript_loaded: Whether transcript was loaded from cache
            
        Returns:
            Tuple of (transcript_path, stats_path)
        """
        # Save detailed transcript
        transcript_filename = f"{base_name}_transcript_{timestamp}.json"
        transcript_path = os.path.join(
            SWEAR_REMOVAL_TRANSCRIPT_OUTPUT_DIR, 
            transcript_filename
        )
        
        transcript_data = {
            'words': word_list,
            'censored_words': [
                {
                    'word': w.get('original_word', w.get('word', '')),
                    'start': w.get('start', 0),
                    'end': w.get('end', 0),
                    'confidence': w.get('conf', 1.0)
                }
                for w in censored_words
            ],
            'statistics': analysis,
            'metadata': {
                'timestamp': timestamp,
                'transcript_loaded_from_cache': transcript_loaded
            }
        }
        
        with open(transcript_path, 'w', encoding='utf-8') as f:
            json.dump(transcript_data, f, indent=2, ensure_ascii=False)
        
        # Save statistics report
        stats_filename = f"{base_name}_statistics_{timestamp}.txt"
        stats_path = os.path.join(
            SWEAR_REMOVAL_STATISTICS_OUTPUT_DIR, 
            stats_filename
        )
        
        report_text = self.stats_generator.generate_report(analysis)
        
        with open(stats_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        logger.info(f"Saved transcript: {transcript_path}")
        logger.info(f"Saved statistics: {stats_path}")
        
        return transcript_path, stats_path
