"""
Audio Cleaner for removing profanity from audio files.

This module wraps monkeyplug's core FFmpeg-based audio cleaning functionality
and integrates it with Whisper-WebUI's architecture.
"""

import os
import subprocess
from typing import Dict, List, Optional, Tuple
from itertools import tee
from modules.utils.logger import get_logger

logger = get_logger()


def pairwise(iterable):
    """Generate pairs of adjacent items from an iterable."""
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


class AudioCleaner:
    """Clean audio files by muting or beeping profanity."""
    
    # Audio format configurations from monkeyplug
    CHANNELS_REPLACER = 'CHANNELS'
    SAMPLE_RATE_REPLACER = 'SAMPLE'
    
    AUDIO_DEFAULT_PARAMS_BY_FORMAT = {
        "flac": ["-c:a", "flac", "-ar", SAMPLE_RATE_REPLACER, "-ac", CHANNELS_REPLACER],
        "m4a": ["-c:a", "aac", "-b:a", "128K", "-ar", SAMPLE_RATE_REPLACER, "-ac", CHANNELS_REPLACER],
        "m4b": ["-c:a", "aac", "-b:a", "128K", "-ar", SAMPLE_RATE_REPLACER, "-ac", CHANNELS_REPLACER, "-f", "ipod"],
        "aac": ["-c:a", "aac", "-b:a", "128K", "-ar", SAMPLE_RATE_REPLACER, "-ac", CHANNELS_REPLACER],
        "mp3": ["-c:a", "libmp3lame", "-b:a", "128K", "-ar", SAMPLE_RATE_REPLACER, "-ac", CHANNELS_REPLACER],
        "ogg": ["-c:a", "libvorbis", "-qscale:a", "5", "-ar", SAMPLE_RATE_REPLACER, "-ac", CHANNELS_REPLACER],
        "opus": ["-c:a", "libopus", "-b:a", "128K", "-ar", SAMPLE_RATE_REPLACER, "-ac", CHANNELS_REPLACER],
        "ac3": ["-c:a", "ac3", "-b:a", "128K", "-ar", SAMPLE_RATE_REPLACER, "-ac", CHANNELS_REPLACER],
        "wav": ["-c:a", "pcm_s16le", "-ar", SAMPLE_RATE_REPLACER, "-ac", CHANNELS_REPLACER],
    }
    
    def __init__(self):
        """Initialize the AudioCleaner."""
        self.beep_hertz = 1000
        self.beep_mix_normalize = False
        self.beep_audio_weight = 1
        self.beep_sine_weight = 1
        self.beep_dropout_transition = 0
    
    def clean_audio(
        self,
        input_path: str,
        output_path: str,
        word_list: List[Dict],
        swears_dict: Dict[str, str],
        beep: bool = False,
        beep_hertz: int = 1000,
        pad_ms_pre: int = 0,
        pad_ms_post: int = 0,
        output_format: str = "MATCH",
        channels: int = 2,
        sample_rate: int = 48000,
        transcript_path: Optional[str] = None,
    ) -> Tuple[str, List[Dict]]:
        """
        Clean audio file by muting or beeping profanity.
        
        Args:
            input_path: Path to input audio file
            output_path: Path to output cleaned audio file
            word_list: List of word dictionaries with timestamps from transcription
            swears_dict: Dictionary of swear words to match
            beep: Whether to beep instead of mute
            beep_hertz: Beep frequency in Hz
            pad_ms_pre: Padding before censored word in milliseconds
            pad_ms_post: Padding after censored word in milliseconds
            output_format: Output format ("MATCH" to match input, or specific format)
            channels: Number of audio channels
            sample_rate: Audio sample rate
            transcript_path: Optional path to save transcript JSON (monkeyplug format)
            
        Returns:
            Tuple of (output_path, censored_words_list)
        """
        # Identify censored words
        censored_words = self.identify_censored_words(word_list, swears_dict)
        
        if not censored_words:
            logger.info("No profanity detected in audio")
            # Just copy the file if no swears found
            if input_path != output_path:
                import shutil
                shutil.copyfile(input_path, output_path)
            return output_path, []
        
        logger.info(f"Found {len(censored_words)} profane words to censor")
        
        # Create mute/beep lists
        pad_sec_pre = pad_ms_pre / 1000.0
        pad_sec_post = pad_ms_post / 1000.0
        
        mute_time_list, sine_time_list, beep_delay_list = self.create_mute_list(
            censored_words,
            pad_sec_pre,
            pad_sec_post,
            beep,
            beep_hertz
        )
        
        # Encode clean audio
        self.encode_clean_audio(
            input_path,
            output_path,
            output_format,
            channels,
            sample_rate,
            mute_time_list,
            sine_time_list,
            beep_delay_list,
            beep,
            word_list,
            transcript_path
        )
        
        return output_path, censored_words
    
    def identify_censored_words(
        self,
        word_list: List[Dict],
        swears_dict: Dict[str, str]
    ) -> List[Dict]:
        """
        Identify which words should be censored.
        
        Args:
            word_list: List of word dictionaries with timestamps
            swears_dict: Dictionary of swear words
            
        Returns:
            List of words that should be censored
        """
        from modules.swear_removal.swear_manager import SwearListManager
        
        censored = []
        for word in word_list:
            word_text = word.get('word', '')
            scrubbed = SwearListManager.scrub_word(word_text)
            
            if scrubbed in swears_dict:
                word['scrub'] = True
                word['original_word'] = word_text
                censored.append(word)
        
        return censored
    
    def create_mute_list(
        self,
        censored_words: List[Dict],
        pad_sec_pre: float,
        pad_sec_post: float,
        beep: bool,
        beep_hertz: int
    ) -> Tuple[List[str], List[str], List[str]]:
        """
        Create FFmpeg filter strings for muting/beeping.
        
        Args:
            censored_words: List of censored word dictionaries
            pad_sec_pre: Padding before word in seconds
            pad_sec_post: Padding after word in seconds
            beep: Whether to use beep instead of mute
            beep_hertz: Beep frequency
            
        Returns:
            Tuple of (mute_list, sine_list, beep_delay_list)
        """
        # Add dummy word at end for pairwise processing
        if censored_words:
            censored_words_copy = censored_words.copy()
            censored_words_copy.append({
                "conf": 1,
                "end": censored_words[-1]["end"] + 2.0,
                "start": censored_words[-1]["end"] + 1.0,
                "word": "dummy",
                "scrub": True,
            })
        else:
            return [], [], []
        
        mute_time_list = []
        sine_time_list = []
        beep_delay_list = []
        
        for word, word_peek in pairwise(censored_words_copy):
            word_start = format(word["start"] - pad_sec_pre, ".3f")
            word_end = format(word["end"] + pad_sec_post, ".3f")
            word_duration = format(float(word_end) - float(word_start), ".3f")
            word_peek_start = format(word_peek["start"] - pad_sec_pre, ".3f")
            
            if beep:
                mute_time_list.append(f"volume=enable='between(t,{word_start},{word_end})':volume=0")
                sine_time_list.append(f"sine=f={beep_hertz}:duration={word_duration}")
                beep_delay_list.append(
                    f"atrim=0:{word_duration},adelay={'|'.join([str(int(float(word_start) * 1000))] * 2)}"
                )
            else:
                mute_time_list.append(
                    f"afade=enable='between(t,{word_start},{word_end})':t=out:st={word_start}:d=5ms"
                )
                mute_time_list.append(
                    f"afade=enable='between(t,{word_end},{word_peek_start})':t=in:st={word_end}:d=5ms"
                )
        
        return mute_time_list, sine_time_list, beep_delay_list
    
    def encode_clean_audio(
        self,
        input_path: str,
        output_path: str,
        output_format: str,
        channels: int,
        sample_rate: int,
        mute_time_list: List[str],
        sine_time_list: List[str],
        beep_delay_list: List[str],
        beep: bool,
        word_list: List[Dict],
        transcript_path: Optional[str] = None
    ) -> None:
        """
        Encode the cleaned audio using FFmpeg.
        
        Args:
            input_path: Input audio file path
            output_path: Output audio file path
            output_format: Output format
            channels: Number of audio channels
            sample_rate: Sample rate
            mute_time_list: List of mute filter strings
            sine_time_list: List of sine wave filter strings
            beep_delay_list: List of beep delay filter strings
            beep: Whether using beep mode
            word_list: List of word dictionaries with timestamps and scrub flags
            transcript_path: Optional path to save transcript JSON
        """
        # Determine output format
        if output_format.upper() == "MATCH":
            ext = os.path.splitext(input_path)[1].lower().lstrip('.')
            output_format = ext
        
        # Get encoding parameters
        audio_params = self._get_audio_params(output_format, channels, sample_rate)
        
        # Build FFmpeg command
        if beep:
            # Beep mode: complex filter with sine waves
            mute_str = ','.join(mute_time_list)
            sine_str = ';'.join([f'{val}[beep{i+1}]' for i, val in enumerate(sine_time_list)])
            beep_delay_str = ';'.join(
                [f'[beep{i+1}]{val}[beep{i+1}_delayed]' for i, val in enumerate(beep_delay_list)]
            )
            beep_mix_str = ''.join([f'[beep{i+1}_delayed]' for i in range(len(beep_delay_list))])
            filter_str = (
                f"[0:a]{mute_str}[mute];{sine_str};{beep_delay_str};"
                f"[mute]{beep_mix_str}amix=inputs={len(beep_delay_list)+1}:"
                f"normalize={str(self.beep_mix_normalize).lower()}:"
                f"dropout_transition={self.beep_dropout_transition}:"
                f"weights={self.beep_audio_weight} {' '.join([str(self.beep_sine_weight)] * len(beep_delay_list))}"
            )
            audio_args = ['-filter_complex', filter_str]
        else:
            # Mute mode: simple audio filter
            audio_args = ['-af', ",".join(mute_time_list)]
        
        ffmpeg_cmd = [
            'ffmpeg',
            '-nostdin',
            '-hide_banner',
            '-nostats',
            '-loglevel', 'error',
            '-y',
            '-i', input_path,
            '-vn', '-sn', '-dn',
        ] + audio_args + audio_params + [output_path]
        
        logger.info(f"Running FFmpeg to clean audio: {' '.join(ffmpeg_cmd[:10])}...")
        
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout
            logger.error(f"FFmpeg failed: {error_msg}")
            raise RuntimeError(f"FFmpeg failed to process audio: {error_msg}")
        
        if not os.path.isfile(output_path):
            raise RuntimeError(f"Output file was not created: {output_path}")
        
        logger.info(f"Successfully created cleaned audio: {output_path}")
        
        # Save transcript if path provided (monkeyplug format)
        if transcript_path:
            self._save_transcript_json(word_list, transcript_path)
    
    def _save_transcript_json(self, word_list: List[Dict], transcript_path: str) -> None:
        """
        Save transcript in monkeyplug-compatible JSON format.
        
        Args:
            word_list: List of words with timestamps and scrub flags
            transcript_path: Path to save JSON file
        """
        import json
        
        # Convert to monkeyplug format (list of word dictionaries)
        transcript_data = []
        for word in word_list:
            word_entry = {
                'word': word.get('word', ''),
                'start': word.get('start', 0),
                'end': word.get('end', 0),
                'conf': word.get('conf', 1.0),
                'scrub': word.get('scrub', False)
            }
            transcript_data.append(word_entry)
        
        with open(transcript_path, 'w', encoding='utf-8') as f:
            json.dump(transcript_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved transcript to: {transcript_path}")
    
    def load_transcript_from_file(self, transcript_path: str) -> Optional[List[Dict]]:
        """
        Load transcript from JSON file (monkeyplug format).
        
        Args:
            transcript_path: Path to transcript JSON file
            
        Returns:
            List of word dictionaries or None if file doesn't exist
        """
        import json
        
        if not os.path.isfile(transcript_path):
            logger.warning(f"Transcript file not found: {transcript_path}")
            return None
        
        try:
            with open(transcript_path, 'r', encoding='utf-8') as f:
                word_list = json.load(f)
            
            logger.info(f"Loaded {len(word_list)} words from transcript: {transcript_path}")
            return word_list
            
        except Exception as e:
            logger.error(f"Failed to load transcript: {e}")
            return None
    
    def _get_audio_params(self, format: str, channels: int, sample_rate: int) -> List[str]:
        """
        Get FFmpeg audio encoding parameters for a format.
        
        Args:
            format: Audio format
            channels: Number of channels
            sample_rate: Sample rate
            
        Returns:
            List of FFmpeg parameters
        """
        format = format.lower().lstrip('.')
        
        if format not in self.AUDIO_DEFAULT_PARAMS_BY_FORMAT:
            logger.warning(f"Unknown format '{format}', defaulting to mp3")
            format = "mp3"
        
        params = self.AUDIO_DEFAULT_PARAMS_BY_FORMAT[format].copy()
        
        # Replace placeholders
        params = [
            {
                self.CHANNELS_REPLACER: str(channels),
                self.SAMPLE_RATE_REPLACER: str(sample_rate),
            }.get(param, param)
            for param in params
        ]
        
        return params
