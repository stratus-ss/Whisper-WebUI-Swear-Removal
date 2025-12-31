"""
Censorship Statistics for analyzing swear removal results.

This module provides functionality to analyze and report on the profanity
censoring process.
"""

from typing import Dict, List, Any
from datetime import datetime


class CensorshipStatistics:
    """Generate statistics and reports for censored audio."""
    
    def __init__(self):
        """Initialize the statistics generator."""
        self.total_words = 0
        self.censored_count = 0
        self.censored_words: List[Dict] = []
        self.audio_duration = 0.0
        self.processing_time = 0.0
    
    def analyze_results(
        self,
        word_list: List[Dict],
        censored_words: List[Dict],
        audio_duration: float = 0.0
    ) -> Dict[str, Any]:
        """
        Analyze censorship results and generate statistics.
        
        Args:
            word_list: Complete list of transcribed words
            censored_words: List of words that were censored
            audio_duration: Total audio duration in seconds
            
        Returns:
            Dictionary containing analysis results
        """
        self.total_words = len(word_list)
        self.censored_count = len(censored_words)
        self.censored_words = censored_words
        self.audio_duration = audio_duration
        
        # Calculate censored duration
        censored_duration = sum(
            word.get('end', 0) - word.get('start', 0)
            for word in censored_words
        )
        
        # Group censored words by unique word
        word_frequency = {}
        for word in censored_words:
            word_text = word.get('original_word', word.get('word', ''))
            word_frequency[word_text] = word_frequency.get(word_text, 0) + 1
        
        return {
            'total_words': self.total_words,
            'censored_count': self.censored_count,
            'censored_percentage': (self.censored_count / self.total_words * 100) if self.total_words > 0 else 0,
            'audio_duration': audio_duration,
            'censored_duration': censored_duration,
            'censored_duration_percentage': (censored_duration / audio_duration * 100) if audio_duration > 0 else 0,
            'unique_censored_words': len(word_frequency),
            'word_frequency': word_frequency,
            'censored_words_detail': [
                {
                    'word': word.get('original_word', word.get('word', '')),
                    'start': round(word.get('start', 0), 3),
                    'end': round(word.get('end', 0), 3),
                    'confidence': round(word.get('conf', word.get('probability', 1.0)), 3)
                }
                for word in censored_words
            ]
        }
    
    def generate_report(self, analysis: Dict[str, Any] = None) -> str:
        """
        Generate a human-readable report.
        
        Args:
            analysis: Analysis dictionary (if None, uses stored data)
            
        Returns:
            Formatted report string
        """
        if analysis is None:
            analysis = {
                'total_words': self.total_words,
                'censored_count': self.censored_count,
                'censored_percentage': (self.censored_count / self.total_words * 100) if self.total_words > 0 else 0,
                'audio_duration': self.audio_duration,
            }
        
        report_lines = [
            "=" * 60,
            "CENSORSHIP STATISTICS REPORT",
            "=" * 60,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "SUMMARY",
            "-" * 60,
            f"Total words transcribed: {analysis['total_words']}",
            f"Words censored: {analysis['censored_count']}",
            f"Censorship rate: {analysis.get('censored_percentage', 0):.2f}%",
            "",
        ]
        
        if 'audio_duration' in analysis and analysis['audio_duration'] > 0:
            report_lines.extend([
                "AUDIO DETAILS",
                "-" * 60,
                f"Total audio duration: {self._format_duration(analysis['audio_duration'])}",
            ])
            
            if 'censored_duration' in analysis:
                report_lines.extend([
                    f"Censored duration: {self._format_duration(analysis['censored_duration'])}",
                    f"Censored time: {analysis.get('censored_duration_percentage', 0):.2f}%",
                ])
            
            report_lines.append("")
        
        if 'word_frequency' in analysis and analysis['word_frequency']:
            report_lines.extend([
                "CENSORED WORDS FREQUENCY",
                "-" * 60,
            ])
            
            # Sort by frequency
            sorted_words = sorted(
                analysis['word_frequency'].items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            for word, count in sorted_words[:20]:  # Top 20
                report_lines.append(f"  {word}: {count} occurrence(s)")
            
            if len(sorted_words) > 20:
                report_lines.append(f"  ... and {len(sorted_words) - 20} more")
            
            report_lines.append("")
        
        if 'censored_words_detail' in analysis and analysis['censored_words_detail']:
            report_lines.extend([
                "CENSORED WORDS TIMELINE",
                "-" * 60,
            ])
            
            for detail in analysis['censored_words_detail'][:50]:  # First 50
                timestamp = self._format_timestamp(detail['start'])
                report_lines.append(
                    f"  [{timestamp}] {detail['word']} "
                    f"(confidence: {detail['confidence']:.2f})"
                )
            
            if len(analysis['censored_words_detail']) > 50:
                report_lines.append(
                    f"  ... and {len(analysis['censored_words_detail']) - 50} more"
                )
        
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)
    
    def generate_json_report(self, analysis: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate a JSON-serializable report.
        
        Args:
            analysis: Analysis dictionary (if None, generates new one)
            
        Returns:
            Dictionary suitable for JSON serialization
        """
        if analysis is None:
            analysis = {
                'total_words': self.total_words,
                'censored_count': self.censored_count,
            }
        
        return {
            'generated_at': datetime.now().isoformat(),
            'statistics': analysis,
            'format_version': '1.0'
        }
    
    @staticmethod
    def _format_duration(seconds: float) -> str:
        """
        Format duration in seconds to human-readable string.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted string (e.g., "1:23:45")
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
    
    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """
        Format timestamp for display.
        
        Args:
            seconds: Timestamp in seconds
            
        Returns:
            Formatted timestamp string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:05.2f}"
        else:
            return f"{minutes}:{secs:05.2f}"
