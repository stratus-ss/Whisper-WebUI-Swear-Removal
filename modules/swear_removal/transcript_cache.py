"""
Transcript caching utilities for swear removal.

This module provides utilities for caching and retrieving transcripts,
eliminating duplication between UI and API implementations.
"""

import os
import json
import glob
import hashlib
from typing import Optional, Dict, List
from modules.utils.logger import get_logger

logger = get_logger()


class TranscriptCache:
    """Manages transcript caching and retrieval."""
    
    def __init__(self, cache_dir: str):
        """
        Initialize transcript cache.
        
        Args:
            cache_dir: Directory where transcripts are stored
        """
        self.cache_dir = cache_dir
        self.registry_path = os.path.join(cache_dir, ".transcript_registry.json")
    
    def calculate_file_hash(self, file_path: str) -> str:
        """
        Calculate SHA256 hash of file.
        
        Args:
            file_path: Path to file
            
        Returns:
            SHA256 hash as hex string
        """
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    
    def load_registry(self) -> Dict[str, str]:
        """
        Load transcript registry.
        
        Migrates from old _transcript_registry.json to new .transcript_registry.json if needed.
        
        Returns:
            Dictionary mapping file hashes to transcript paths
        """
        # Check for old registry file and migrate
        old_registry_path = os.path.join(self.cache_dir, "_transcript_registry.json")
        if os.path.exists(old_registry_path) and not os.path.exists(self.registry_path):
            try:
                with open(old_registry_path, 'r', encoding='utf-8') as f:
                    registry = json.load(f)
                # Try to save to new location
                self.save_registry(registry)
                logger.info("Migrated registry from _transcript_registry.json to .transcript_registry.json")
                # Try to remove old file (but don't fail if we can't)
                try:
                    os.remove(old_registry_path)
                except:
                    logger.warning(f"Could not remove old registry file: {old_registry_path}")
                return registry
            except Exception as e:
                logger.warning(f"Failed to migrate old registry: {e}")
        
        # Load from current registry path
        if not os.path.exists(self.registry_path):
            return {}
        
        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load registry: {e}")
            return {}
    
    def save_registry(self, registry: Dict[str, str]) -> None:
        """
        Save transcript registry.
        
        Args:
            registry: Dictionary mapping file hashes to transcript paths
        
        Raises:
            OSError: If file cannot be written due to permissions or other IO error
        """
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            
            # Write to temp file first, then atomic rename
            temp_path = self.registry_path + '.tmp'
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(registry, f, indent=2, ensure_ascii=False)
            
            # Atomic rename (or as atomic as possible)
            os.replace(temp_path, self.registry_path)
            
        except PermissionError as e:
            logger.error(f"Permission denied writing registry: {self.registry_path}")
            logger.error(f"Please ensure the directory is writable by the current user")
            raise OSError(f"Cannot write registry file (permission denied): {self.registry_path}") from e
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")
            # Clean up temp file if it exists
            temp_path = self.registry_path + '.tmp'
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            raise
    
    def find_transcript_by_hash(self, file_hash: str) -> Optional[str]:
        """
        Find cached transcript by file hash.
        
        Args:
            file_hash: SHA256 hash of the audio file
            
        Returns:
            Path to transcript file, or None if not found
        """
        registry = self.load_registry()
        
        if file_hash in registry:
            transcript_path = registry[file_hash]
            if os.path.exists(transcript_path):
                logger.info(f"Found transcript by hash: {transcript_path}")
                return transcript_path
            else:
                logger.warning(f"Registry entry exists but file not found: {transcript_path}")
        
        return None
    
    def find_transcript_by_filename(self, base_name: str) -> Optional[str]:
        """
        Find transcript by filename pattern (fallback method).
        
        Args:
            base_name: Base name of the audio file (without extension)
            
        Returns:
            Path to most recent matching transcript, or None if not found
        """
        pattern = os.path.join(self.cache_dir, f"{base_name}_transcript_*.json")
        matches = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
        
        if matches:
            logger.info(f"Found transcript by filename: {matches[0]}")
            return matches[0]
        
        return None
    
    def find_transcript(self, file_path: str, base_name: str) -> Optional[str]:
        """
        Find cached transcript by hash or filename.
        
        Tries hash-based lookup first, then falls back to filename pattern matching.
        
        Args:
            file_path: Path to the audio file
            base_name: Base name of the audio file (without extension)
        
        Returns:
            Path to transcript file, or None if not found
        """
        # Try hash-based lookup first
        file_hash = self.calculate_file_hash(file_path)
        transcript_path = self.find_transcript_by_hash(file_hash)
        
        if transcript_path:
            return transcript_path
        
        # Fallback to filename-based search
        return self.find_transcript_by_filename(base_name)
    
    def register_transcript(
        self, 
        file_path: str, 
        transcript_path: str
    ) -> None:
        """
        Register a new transcript in the cache.
        
        Args:
            file_path: Path to the audio file
            transcript_path: Path to the transcript file
        """
        file_hash = self.calculate_file_hash(file_path)
        registry = self.load_registry()
        registry[file_hash] = transcript_path
        self.save_registry(registry)
        logger.info(f"Registered transcript for hash {file_hash[:8]}...")
    
    def load_transcript_file(self, transcript_path: str) -> Optional[List[Dict]]:
        """
        Load transcript from file.
        
        Args:
            transcript_path: Path to transcript JSON file
            
        Returns:
            List of word dictionaries, or None if failed
        """
        try:
            with open(transcript_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Handle different transcript formats
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'words' in data:
                return data['words']
            else:
                logger.warning(f"Unexpected transcript format in {transcript_path}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to load transcript from {transcript_path}: {e}")
            return None
    
    def save_transcript_file(
        self, 
        transcript_path: str, 
        word_list: List[Dict],
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Save transcript to file.
        
        Args:
            transcript_path: Path where transcript should be saved
            word_list: List of word dictionaries
            metadata: Optional metadata to include
        """
        os.makedirs(os.path.dirname(transcript_path), exist_ok=True)
        
        data = {
            'words': word_list
        }
        
        if metadata:
            data['metadata'] = metadata
        
        with open(transcript_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved transcript with {len(word_list)} words to {transcript_path}")
