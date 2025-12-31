"""
Swear List Manager for loading and managing profanity lists.

This module provides functionality to load, manage, and validate swear word lists
in both text and JSON formats.
"""

import json
import os
import string
from typing import Dict, List, Optional
from modules.utils.logger import get_logger

logger = get_logger()


class SwearListManager:
    """Manages swear word lists for audio cleaning."""
    
    def __init__(self, default_list_path: Optional[str] = None):
        """
        Initialize the SwearListManager.
        
        Args:
            default_list_path: Path to the default swear list file.
                             If None, uses the bundled default list.
        """
        self.default_list_path = default_list_path or self._get_default_list_path()
        self.custom_lists: Dict[str, str] = {}
        self._swears_cache: Dict[str, Dict[str, str]] = {}
        
    @staticmethod
    def _get_default_list_path() -> str:
        """Get the path to the default swear list."""
        return os.path.join(
            os.path.dirname(__file__),
            "data",
            "default_swears.txt"
        )
    
    @staticmethod
    def scrub_word(value: str) -> str:
        """
        Clean and normalize a word for comparison.
        
        Args:
            value: Word to clean
            
        Returns:
            Normalized word in lowercase without punctuation
        """
        return str(value).lower().strip().translate(str.maketrans('', '', string.punctuation))
    
    def load_default_list(self) -> Dict[str, str]:
        """
        Load the default swear list.
        
        Returns:
            Dictionary mapping normalized words to replacement values
        """
        if "default" not in self._swears_cache:
            self._swears_cache["default"] = self._load_list_from_file(self.default_list_path)
        return self._swears_cache["default"]
    
    def load_custom_list(self, file_path: str, list_id: str = "custom") -> Dict[str, str]:
        """
        Load a custom swear list from a file.
        
        Args:
            file_path: Path to the swear list file (text or JSON)
            list_id: Identifier for this custom list
            
        Returns:
            Dictionary mapping normalized words to replacement values
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Swear list file not found: {file_path}")
        
        self.custom_lists[list_id] = file_path
        swears_dict = self._load_list_from_file(file_path)
        self._swears_cache[list_id] = swears_dict
        
        logger.info(f"Loaded custom swear list '{list_id}' with {len(swears_dict)} words")
        return swears_dict
    
    def _load_list_from_file(self, file_path: str) -> Dict[str, str]:
        """
        Load swear list from either text or JSON format.
        
        Args:
            file_path: Path to the swear list file
            
        Returns:
            Dictionary mapping normalized words to replacement values
        """
        if self._is_json_file(file_path):
            return self._load_from_json(file_path)
        else:
            return self._load_from_text(file_path)
    
    def _is_json_file(self, file_path: str) -> bool:
        """
        Detect if file is JSON format.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file appears to be JSON
        """
        if file_path.lower().endswith('.json'):
            return True
        
        # Try to parse first few lines as JSON
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(100)
                content = content.strip()
                if content.startswith('[') or content.startswith('{'):
                    # Read full content and try to parse
                    f.seek(0)
                    json.loads(f.read())
                    return True
        except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
            pass
        
        return False
    
    def _load_from_json(self, file_path: str) -> Dict[str, str]:
        """
        Load swears from JSON format.
        
        Expected format: ["word1", "word2", "word3", ...]
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Dictionary mapping normalized words to replacement values
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            raise ValueError(f"JSON swears file must contain an array of strings, got {type(data).__name__}")
        
        swears_dict = {}
        for item in data:
            if isinstance(item, str) and item.strip():
                swears_dict[self.scrub_word(item)] = "*****"
        
        return swears_dict
    
    def _load_from_text(self, file_path: str) -> Dict[str, str]:
        """
        Load swears from pipe-delimited text format.
        
        Format: word|replacement (or just word for default replacement)
        
        Args:
            file_path: Path to text file
            
        Returns:
            Dictionary mapping normalized words to replacement values
        """
        swears_dict = {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [line.rstrip("\n") for line in f]
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split("|")
            word = parts[0].strip()
            replacement = parts[1].strip() if len(parts) > 1 else "*****"
            
            if word:
                swears_dict[self.scrub_word(word)] = replacement
        
        return swears_dict
    
    def get_swears_dict(self, list_id: str = "default") -> Dict[str, str]:
        """
        Get a swear dictionary by ID.
        
        Args:
            list_id: ID of the list to retrieve ("default" or custom ID)
            
        Returns:
            Dictionary mapping normalized words to replacement values
        """
        if list_id == "default":
            return self.load_default_list()
        elif list_id in self._swears_cache:
            return self._swears_cache[list_id]
        elif list_id in self.custom_lists:
            return self.load_custom_list(self.custom_lists[list_id], list_id)
        else:
            raise ValueError(f"Swear list '{list_id}' not found")
    
    def save_custom_list(self, words: List[str], path: str, format: str = "text") -> None:
        """
        Save a custom swear list to file.
        
        Args:
            words: List of words to save
            path: Output file path
            format: Format to save in ("text" or "json")
        """
        if format == "json":
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(words, f, indent=2, ensure_ascii=False)
        else:
            with open(path, 'w', encoding='utf-8') as f:
                for word in words:
                    f.write(f"{word}\n")
        
        logger.info(f"Saved {len(words)} words to {path}")
    
    def get_available_lists(self) -> List[str]:
        """
        Get list of available swear list IDs.
        
        Returns:
            List of available list IDs
        """
        return ["default"] + list(self.custom_lists.keys())
    
    def backup_default_list(self) -> str:
        """
        Create a backup of the default swear list.
        
        Returns:
            Path to the backup file
        """
        import shutil
        from datetime import datetime
        
        backup_dir = os.path.join(os.path.dirname(self.default_list_path), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"default_swears_backup_{timestamp}.txt"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        shutil.copy2(self.default_list_path, backup_path)
        logger.info(f"Created backup at: {backup_path}")
        
        return backup_path
    
    def get_latest_backup(self) -> Optional[str]:
        """
        Get the path to the most recent backup file.
        
        Returns:
            Path to the latest backup, or None if no backups exist
        """
        backup_dir = os.path.join(os.path.dirname(self.default_list_path), "backups")
        
        if not os.path.exists(backup_dir):
            return None
        
        backups = [
            os.path.join(backup_dir, f)
            for f in os.listdir(backup_dir)
            if f.startswith("default_swears_backup_") and f.endswith(".txt")
        ]
        
        if not backups:
            return None
        
        # Sort by modification time, most recent first
        backups.sort(key=os.path.getmtime, reverse=True)
        return backups[0]
    
    def restore_from_backup(self, backup_path: Optional[str] = None) -> bool:
        """
        Restore the default swear list from a backup.
        
        Args:
            backup_path: Path to backup file. If None, uses the latest backup.
            
        Returns:
            True if restore was successful, False otherwise
        """
        import shutil
        
        if backup_path is None:
            backup_path = self.get_latest_backup()
        
        if backup_path is None or not os.path.exists(backup_path):
            logger.error("No backup file found to restore from")
            return False
        
        try:
            shutil.copy2(backup_path, self.default_list_path)
            # Clear cache so the restored list is loaded on next use
            if "default" in self._swears_cache:
                del self._swears_cache["default"]
            
            logger.info(f"Restored default list from: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")
            return False
    
    def save_to_default_list(self, words: List[str]) -> bool:
        """
        Save edited words to the default swear list file.
        Creates a backup before overwriting.
        
        Args:
            words: List of words to save
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            # Create backup before overwriting
            self.backup_default_list()
            
            # Save to default list file
            with open(self.default_list_path, 'w', encoding='utf-8') as f:
                for word in words:
                    word = word.strip()
                    if word:
                        f.write(f"{word}\n")
            
            # Clear cache so the new list is loaded on next use
            if "default" in self._swears_cache:
                del self._swears_cache["default"]
            
            logger.info(f"Saved {len(words)} words to default list")
            return True
        except Exception as e:
            logger.error(f"Failed to save to default list: {e}")
            return False