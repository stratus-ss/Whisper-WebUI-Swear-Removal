"""
Swear Removal Tab Module

This module contains all UI and logic for the swear removal feature.
Isolated from main app.py to minimize merge conflicts with upstream updates.
"""
import os
import json
import glob
import hashlib
import tempfile
import subprocess
from datetime import datetime

import gradio as gr
from gradio_i18n import gettext as _

try:
    import soundfile as sf
except ImportError:
    sf = None

from modules.utils.paths import (
    SWEAR_REMOVAL_AUDIO_OUTPUT_DIR, 
    SWEAR_REMOVAL_TRANSCRIPT_OUTPUT_DIR, 
    SWEAR_REMOVAL_STATISTICS_OUTPUT_DIR
)
from modules.utils.logger import get_logger
from modules.utils.platform_utils import PlatformHelper
from modules.swear_removal.transcript_cache import TranscriptCache
from modules.swear_removal.swear_service import SwearRemovalService

logger = get_logger()


class SwearRemovalTab:
    """Handles swear removal tab UI and processing logic."""
    
    def __init__(self, app):
        """
        Initialize the swear removal tab.
        
        Args:
            app: Reference to main App instance with whisper_inf, swear_manager, etc.
        """
        self.app = app
        self.components = {}
    
    def render(self):
        """Render the swear removal tab UI and return components."""
        with gr.Column():
            self.components['files_audio'] = gr.Files(
                type="filepath", 
                label=_("Upload Audio/Video Files")
            )
            
            # Swear list management
            with gr.Accordion(_("Swear List Settings"), open=True):
                self.components['rd_swear_list_mode'] = gr.Radio(
                    choices=["Default List", "Upload Custom List", "Edit Default List"],
                    value="Default List",
                    label=_("Swear List Mode")
                )
                self.components['file_custom_swears'] = gr.File(
                    label=_("Upload Custom Swear List (txt or json)"),
                    visible=False
                )
                self.components['btn_save_custom_as_default'] = gr.Button(
                    _("💾 Save This Custom List as New Default"),
                    variant="primary",
                    visible=False,
                    size="sm"
                )
                self.components['tb_edit_swears'] = gr.Textbox(
                    label=_("Edit Swear List (one per line)"),
                    lines=10,
                    visible=False,
                    placeholder="Enter swear words, one per line..."
                )
                with gr.Row(visible=False) as self.components['row_edit_buttons']:
                    self.components['btn_load_default'] = gr.Button(
                        _("Load Default List"),
                        scale=1
                    )
                    self.components['btn_save_default'] = gr.Button(
                        _("Save to Default List"),
                        variant="primary",
                        scale=1
                    )
                    self.components['btn_restore_default'] = gr.Button(
                        _("Restore Original List"),
                        variant="secondary",
                        scale=1
                    )
            
            # Transcription options
            with gr.Accordion(_("Transcription Options"), open=True):
                self.components['cb_reuse_transcript'] = gr.Checkbox(
                    label=_("Reuse existing transcript if available"),
                    value=True,
                    info="Skip re-transcription and use cached transcript for faster processing"
                )
            
            # Censoring options
            with gr.Accordion(_("Censoring Options"), open=False):
                self.components['rd_censor_mode'] = gr.Radio(
                    choices=["Mute", "Beep"],
                    value="Mute",
                    label=_("Censor Mode")
                )
                self.components['nb_beep_hertz'] = gr.Number(
                    label="Beep Frequency (Hz)",
                    value=1000,
                    precision=0,
                    visible=False
                )
                self.components['nb_pad_pre'] = gr.Number(
                    label="Padding Before (ms)",
                    value=0,
                    precision=0
                )
                self.components['nb_pad_post'] = gr.Number(
                    label="Padding After (ms)",
                    value=0,
                    precision=0
                )
                self.components['dd_output_format'] = gr.Dropdown(
                    label=_("Output Format"),
                    choices=["MATCH", "mp3", "wav", "flac", "m4a", "m4b", "aac", "ogg", "opus", "ac3"],
                    value="MATCH"
                )
            
            self.components['btn_run'] = gr.Button(
                _("REMOVE SWEARS FROM AUDIO"), 
                variant="primary"
            )
            
            # Cache management buttons
            with gr.Row():
                self.components['btn_clear_audio_cache'] = gr.Button(
                    _("Clear Audio Cache"),
                    variant="secondary",
                    size="sm"
                )
                self.components['btn_clear_transcript_cache'] = gr.Button(
                    _("Clear Transcript Cache"),
                    variant="secondary",
                    size="sm"
                )
            
            with gr.Column():
                self.components['tb_indicator'] = gr.Textbox(
                    label=_("Processing Status"), 
                    scale=5, 
                    lines=3
                )
                
                with gr.Row():
                    self.components['ad_output'] = gr.Audio(
                        label=_("Cleaned Audio Preview"), 
                        scale=8
                    )
                    self.components['btn_open_folder'] = gr.Button('📂', scale=1)
                
                self.components['tb_statistics'] = gr.Textbox(
                    label=_("Censorship Statistics"),
                    lines=15
                )
                
                self.components['tb_transcript_info'] = gr.Textbox(
                    label=_("Processing Info"),
                    lines=3
                )
                
                self.components['files_output'] = gr.Files(
                    label=_("Downloadable Files (audio + transcript + stats)"),
                    interactive=False
                )
        
        return self.components
    
    def register_events(self):
        """Register all event handlers for the tab."""
        c = self.components
        
        # Swear list mode change
        c['rd_swear_list_mode'].change(
            fn=self._update_swear_list_visibility,
            inputs=[c['rd_swear_list_mode']],
            outputs=[c['file_custom_swears'], c['btn_save_custom_as_default'], c['tb_edit_swears'], c['row_edit_buttons']]
        )
        
        # Censor mode change
        c['rd_censor_mode'].change(
            fn=self._update_beep_visibility,
            inputs=[c['rd_censor_mode']],
            outputs=[c['nb_beep_hertz']]
        )
        
        # Load default list button
        c['btn_load_default'].click(
            fn=self._load_default_list_to_editor,
            inputs=None,
            outputs=[c['tb_edit_swears']]
        )
        
        # Save to default list button
        c['btn_save_default'].click(
            fn=self._save_to_default_list,
            inputs=[c['tb_edit_swears']],
            outputs=[c['tb_indicator']]
        )
        
        # Restore original list button
        c['btn_restore_default'].click(
            fn=self._restore_original_list,
            inputs=None,
            outputs=[c['tb_indicator'], c['tb_edit_swears']]
        )
        
        # Save custom uploaded list as default
        c['btn_save_custom_as_default'].click(
            fn=self._save_uploaded_as_default,
            inputs=[c['file_custom_swears']],
            outputs=[c['tb_indicator']]
        )
        
        # Main processing button
        c['btn_run'].click(
            fn=self.remove_swears_from_files,
            inputs=[
                c['files_audio'],
                c['rd_swear_list_mode'],
                c['file_custom_swears'],
                c['tb_edit_swears'],
                c['rd_censor_mode'],
                c['nb_beep_hertz'],
                c['nb_pad_pre'],
                c['nb_pad_post'],
                c['dd_output_format'],
                c['cb_reuse_transcript']
            ],
            outputs=[
                c['tb_indicator'], 
                c['ad_output'], 
                c['tb_statistics'], 
                c['tb_transcript_info'], 
                c['files_output']
            ],
            show_progress="full",  # Enable progress tracking
            show_progress_on=[c['tb_indicator']]  # Only display progress in status indicator
        )
        
        # Open folder button - shows path in UI for Docker/headless environments
        c['btn_open_folder'].click(
            fn=lambda: PlatformHelper.open_folder(SWEAR_REMOVAL_AUDIO_OUTPUT_DIR),
            inputs=None,
            outputs=c['tb_indicator']
        )
        
        # Clear audio cache button
        c['btn_clear_audio_cache'].click(
            fn=self.clear_audio_cache,
            inputs=None,
            outputs=[c['tb_indicator']]
        )
        
        # Clear transcript cache button
        c['btn_clear_transcript_cache'].click(
            fn=self.clear_transcript_cache,
            inputs=None,
            outputs=[c['tb_indicator']]
        )
    
    def _update_swear_list_visibility(self, mode):
        """Update visibility of swear list UI components."""
        return {
            self.components['file_custom_swears']: gr.update(visible=(mode == "Upload Custom List")),
            self.components['btn_save_custom_as_default']: gr.update(visible=(mode == "Upload Custom List")),
            self.components['tb_edit_swears']: gr.update(visible=(mode == "Edit Default List")),
            self.components['row_edit_buttons']: gr.update(visible=(mode == "Edit Default List"))
        }
    
    def _update_beep_visibility(self, mode):
        """Update visibility of beep frequency control."""
        return gr.update(visible=(mode == "Beep"))
    
    def _load_default_list_to_editor(self):
        """Load default swear list into editor."""
        swears_dict = self.app.swear_manager.load_default_list()
        words = '\n'.join(sorted(swears_dict.keys()))
        return words
    
    def _save_to_default_list(self, edit_swears_text):
        """
        Save edited swear list to the default swear list file.
        Creates a backup before overwriting.
        
        Args:
            edit_swears_text: Text from the editor textbox
            
        Returns:
            str: Status message
        """
        if not edit_swears_text or not edit_swears_text.strip():
            return "❌ Cannot save empty list"
        
        try:
            # Parse words from text
            words = [
                line.strip()
                for line in edit_swears_text.strip().split('\n')
                if line.strip() and not line.strip().startswith('#')
            ]
            
            if not words:
                return "❌ No valid words to save"
            
            # Save to default list (automatically creates backup)
            success = self.app.swear_manager.save_to_default_list(words)
            
            if success:
                message = f"✓ Saved {len(words)} words to default list\n"
                message += "✓ Backup created automatically\n"
                message += "Changes will be used for all future processing"
                logger.info(f"User saved {len(words)} words to default swear list")
                return message
            else:
                return "❌ Failed to save to default list. Check logs for details."
                
        except Exception as e:
            error_msg = f"❌ Error saving to default list: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg
    
    def _restore_original_list(self):
        """
        Restore the default swear list from the most recent backup.
        
        Returns:
            Tuple of (status_message, restored_text)
        """
        try:
            # Get latest backup
            backup_path = self.app.swear_manager.get_latest_backup()
            
            if not backup_path:
                message = "❌ No backup found\n"
                message += "Backups are created automatically when you save changes"
                return message, ""
            
            # Show backup info
            backup_time = datetime.fromtimestamp(os.path.getmtime(backup_path))
            backup_name = os.path.basename(backup_path)
            
            # Restore from backup
            success = self.app.swear_manager.restore_from_backup(backup_path)
            
            if success:
                # Load the restored list into editor
                swears_dict = self.app.swear_manager.load_default_list()
                words = '\n'.join(sorted(swears_dict.keys()))
                
                message = f"✓ Restored from backup: {backup_name}\n"
                message += f"✓ Backup date: {backup_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                message += f"✓ Loaded {len(swears_dict)} words\n"
                message += "Default list has been restored"
                
                logger.info(f"User restored default swear list from backup: {backup_name}")
                return message, words
            else:
                return "❌ Failed to restore from backup. Check logs for details.", ""
                
        except Exception as e:
            error_msg = f"❌ Error restoring from backup: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg, ""
    
    def _save_uploaded_as_default(self, custom_swear_file):
        """
        Save an uploaded custom swear list as the new default list.
        Creates a backup before overwriting.
        
        Args:
            custom_swear_file: Uploaded file object
            
        Returns:
            str: Status message
        """
        if not custom_swear_file:
            return "❌ Please upload a custom swear list file first"
        
        try:
            file_path = custom_swear_file.name if hasattr(custom_swear_file, 'name') else custom_swear_file
            
            if not os.path.exists(file_path):
                return "❌ Uploaded file not found"
            
            # Load the custom list to validate it and get word count
            try:
                swears_dict = self.app.swear_manager.load_custom_list(file_path, "temp_validate")
                words = list(swears_dict.keys())
            except Exception as e:
                return f"❌ Invalid swear list file: {str(e)}"
            
            if not words:
                return "❌ The uploaded file contains no valid words"
            
            # Save to default list (automatically creates backup)
            success = self.app.swear_manager.save_to_default_list(words)
            
            if success:
                message = f"✓ Saved custom list as new default!\n"
                message += f"✓ {len(words)} words imported\n"
                message += "✓ Backup of old default created automatically\n"
                message += "✓ This list will now be used as the default for all future processing"
                
                filename = os.path.basename(file_path)
                logger.info(f"User saved uploaded custom list ({filename}) as default: {len(words)} words")
                return message
            else:
                return "❌ Failed to save as default list. Check logs for details."
                
        except Exception as e:
            error_msg = f"❌ Error saving uploaded list as default: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg
    
    def clear_audio_cache(self):
        """
        Clear all cached audio files from the swear removal audio output directory.
        
        Returns:
            str: Status message indicating the result
        """
        try:
            deleted_count = 0
            total_size = 0
            
            if os.path.exists(SWEAR_REMOVAL_AUDIO_OUTPUT_DIR):
                for filename in os.listdir(SWEAR_REMOVAL_AUDIO_OUTPUT_DIR):
                    file_path = os.path.join(SWEAR_REMOVAL_AUDIO_OUTPUT_DIR, filename)
                    
                    # Skip directories and placeholder files
                    if os.path.isfile(file_path):
                        try:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            deleted_count += 1
                            total_size += file_size
                            logger.info(f"Deleted audio cache file: {filename}")
                        except Exception as e:
                            logger.error(f"Failed to delete {filename}: {e}")
            
            size_mb = total_size / (1024 * 1024)
            message = "✓ Audio cache cleared!\n"
            message += f"Deleted {deleted_count} file(s) ({size_mb:.2f} MB)"
            logger.info(message)
            return message
            
        except Exception as e:
            error_msg = f"Error clearing audio cache: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg
    
    def clear_transcript_cache(self):
        """
        Clear all cached transcript files and the transcript registry.
        
        Returns:
            str: Status message indicating the result
        """
        try:
            deleted_count = 0
            total_size = 0
            registry_deleted = False
            
            if os.path.exists(SWEAR_REMOVAL_TRANSCRIPT_OUTPUT_DIR):
                for filename in os.listdir(SWEAR_REMOVAL_TRANSCRIPT_OUTPUT_DIR):
                    file_path = os.path.join(SWEAR_REMOVAL_TRANSCRIPT_OUTPUT_DIR, filename)
                    
                    # Skip directories
                    if os.path.isfile(file_path):
                        try:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            deleted_count += 1
                            total_size += file_size
                            
                            if filename == "_transcript_registry.json":
                                registry_deleted = True
                                logger.info("Deleted transcript registry")
                            else:
                                logger.info(f"Deleted transcript cache file: {filename}")
                        except Exception as e:
                            logger.error(f"Failed to delete {filename}: {e}")
            
            size_mb = total_size / (1024 * 1024)
            message = "✓ Transcript cache cleared!\n"
            message += f"Deleted {deleted_count} file(s) ({size_mb:.2f} MB)\n"
            
            if registry_deleted:
                message += "Registry cleared - transcripts will be regenerated on next run"
            
            logger.info(message)
            return message
            
        except Exception as e:
            error_msg = f"Error clearing transcript cache: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg
    
    def _load_swear_list(self, mode, custom_file, edit_text, progress):
        """
        Load appropriate swear list based on mode.
        
        Args:
            mode: Swear list mode selection
            custom_file: Custom swear list file
            edit_text: Edited swear list text
            progress: Gradio progress indicator
            
        Returns:
            Dictionary of swear words, or error string
        """
        progress(0, desc="Loading swear list...")
        
        try:
            if mode == "Upload Custom List" and custom_file:
                return self.app.swear_manager.load_custom_list(
                    custom_file.name, 
                    "custom_upload"
                )
            elif mode == "Edit Default List" and edit_text:
                return self._load_edited_list(edit_text)
            else:
                return self.app.swear_manager.load_default_list()
                
        except Exception as e:
            logger.error(f"Failed to load swear list: {e}")
            return f"Error loading swear list: {str(e)}"
    
    def _load_edited_list(self, edit_text):
        """
        Load swear list from edited text.
        
        Args:
            edit_text: Edited swear list as text
            
        Returns:
            Dictionary of swear words
        """
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False, encoding='utf-8'
        ) as f:
            for line in edit_text.strip().split('\n'):
                if line.strip():
                    f.write(f"{line.strip()}\n")
            temp_path = f.name
        
        try:
            return self.app.swear_manager.load_custom_list(temp_path, "custom_edited")
        finally:
            os.remove(temp_path)
    
    def _get_transcript(self, file_path, base_name, reuse_transcript, progress, file_idx, total_files):
        """
        Get transcript from cache or transcribe.
        
        Args:
            file_path: Path to audio file
            base_name: Base name of file
            reuse_transcript: Whether to try loading cached transcript
            progress: Gradio progress indicator
            file_idx: Current file index
            total_files: Total number of files
            
        Returns:
            Tuple of (word_list, transcript_loaded)
        """
        if reuse_transcript:
            cached = self._try_load_cached_transcript(file_path, base_name, progress, file_idx, total_files)
            if cached:
                return cached, True
        
        # Transcribe
        progress((file_idx / total_files) * 0.9 + 0.1, desc=f"Transcribing {base_name}...")
        segments, _ = self.app.whisper_inf.transcribe(audio=file_path)
        word_list = self._extract_words_from_segments(segments)
        
        return word_list, False
    
    def _try_load_cached_transcript(self, file_path, base_name, progress, file_idx, total_files):
        """
        Try to load cached transcript.
        
        Args:
            file_path: Path to audio file
            base_name: Base name of file
            progress: Gradio progress indicator
            file_idx: Current file index
            total_files: Total number of files
            
        Returns:
            Word list if found, None otherwise
        """
        cache = TranscriptCache(SWEAR_REMOVAL_TRANSCRIPT_OUTPUT_DIR)
        transcript_path = cache.find_transcript(file_path, base_name)
        
        if transcript_path:
            progress((file_idx / total_files) * 0.9 + 0.1, desc=f"Loading existing transcript for {base_name}...")
            logger.info(f"Attempting to load transcript: {transcript_path}")
            
            word_list = self.app.audio_cleaner.load_transcript_from_file(transcript_path)
            
            if word_list:
                logger.info(f"✓ Loaded transcript with {len(word_list)} words (skipping re-transcription)")
                return word_list
            else:
                logger.warning("Failed to load transcript, will re-transcribe")
        
        return None
    
    def _extract_words_from_segments(self, segments):
        """
        Extract word-level data from transcription segments.
        
        Args:
            segments: Transcription segments
            
        Returns:
            List of word dictionaries
        """
        word_list = []
        
        for segment in segments:
            if not hasattr(segment, 'words') or not segment.words:
                continue
            
            for word_data in segment.words:
                word_list.append({
                    'word': self._extract_word_text(word_data.word),
                    'start': word_data.start,
                    'end': word_data.end,
                    'conf': getattr(word_data, 'probability', 1.0)
                })
        
        return word_list
    
    def _extract_word_text(self, word):
        """
        Extract word text handling various formats.
        
        Args:
            word: Word object or string
            
        Returns:
            Cleaned word text
        """
        if hasattr(word, 'strip'):
            return word.strip()
        return str(word).strip()
        
    def _get_audio_duration(self, file_path):
        """
        Get audio duration using FFprobe.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Duration in seconds
        """
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                 '-of', 'default=noprint_wrappers=1:nokey=1', file_path],
                capture_output=True,
                text=True,
                check=True
            )
            return float(result.stdout.strip())
        except Exception as e:
            logger.warning(f"Failed to get duration with FFprobe: {e}")
            return self._get_duration_fallback(file_path)
    
    def _get_duration_fallback(self, file_path):
        """
        Fallback method to get audio duration.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Duration in seconds
        """
        try:
            if sf is not None:
                audio_data, sample_rate = sf.read(file_path)
                return len(audio_data) / sample_rate
            else:
                logger.error("soundfile not available")
                return 0.0
        except Exception as e:
            logger.error(f"Failed to get audio duration: {e}")
            return 0.0
        
    def _process_single_file(self, file, swears_dict, censor_mode, beep_hertz, pad_pre, pad_post, output_format, reuse_transcript, progress, file_idx, total_files):
        """
        Process a single file for swear removal.
        
        Args:
            file: File object
            swears_dict: Dictionary of swear words
            censor_mode: "Mute" or "Beep"
            beep_hertz: Beep frequency
            pad_pre: Pre-padding in ms
            pad_post: Post-padding in ms
            output_format: Output format
            reuse_transcript: Whether to reuse cached transcript
            progress: Gradio progress indicator
            file_idx: Current file index
            total_files: Total number of files
            
        Returns:
            Dictionary with processing results
        """
        file_path = file.name if hasattr(file, 'name') else file
        original_filename = os.path.basename(file_path)
        base_name = os.path.splitext(original_filename)[0]
        
        logger.info(f"Processing file: {original_filename} (base_name: {base_name})")
        
        # Get or create transcript
        word_list, transcript_loaded = self._get_transcript(
            file_path, base_name, reuse_transcript, progress, file_idx, total_files
        )
        
        if not word_list:
            logger.warning(f"No words extracted from {base_name}, skipping")
            return {'error': f"No words extracted from {base_name}"}
        
        # Prepare output paths using service
        service = SwearRemovalService()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = service.get_output_filename(base_name, timestamp, output_format, file_path)
        output_path = os.path.join(SWEAR_REMOVAL_AUDIO_OUTPUT_DIR, output_filename)
        
        # Prepare transcript path
        transcript_path = None
        if not transcript_loaded:
            transcript_path = os.path.join(
                SWEAR_REMOVAL_TRANSCRIPT_OUTPUT_DIR,
                f"{base_name}_transcript_{timestamp}.json"
            )
        
        # Clean audio
        progress((file_idx / total_files) * 0.9 + 0.3, desc=f"Cleaning audio {base_name}...")
        cleaned_path, censored_words = self.app.audio_cleaner.clean_audio(
            input_path=file_path,
            output_path=output_path,
            word_list=word_list,
            swears_dict=swears_dict,
            beep=(censor_mode == "Beep"),
            beep_hertz=int(beep_hertz) if beep_hertz else 1000,
            pad_ms_pre=int(pad_pre) if pad_pre else 0,
            pad_ms_post=int(pad_post) if pad_post else 0,
            output_format=output_format,
            transcript_path=transcript_path,
        )
        
        # Get audio duration and generate statistics
        audio_duration = self._get_audio_duration(file_path)
        analysis = self.app.stats_generator.analyze_results(word_list, censored_words, audio_duration)
        
        # Save statistics files using service
        transcript_path_saved, stats_path = service.save_statistics_files(
            base_name, timestamp, word_list, censored_words, analysis, transcript_loaded
        )
        stats_files = [transcript_path_saved, stats_path]
        report_text = service.stats_generator.generate_report(analysis)
        
        # Register transcript in cache
        if not transcript_loaded and transcript_path and os.path.exists(transcript_path):
            try:
                cache = TranscriptCache(SWEAR_REMOVAL_TRANSCRIPT_OUTPUT_DIR)
                cache.register_transcript(file_path, transcript_path)
            except OSError as e:
                logger.warning(f"Could not register transcript in cache: {e}")
                logger.warning("Transcript saved successfully but cache registry update failed")
            stats_files.append(transcript_path)
        
        logger.info(f"✓ Successfully processed {base_name}: {len(censored_words)} words censored")
        
        return {
            'audio_path': cleaned_path,
            'stats_files': stats_files,
            'report_text': report_text,
            'base_name': base_name
        }
    
    def _build_info_message(self, file_count, output_count):
        """
        Build processing info message.
        
        Args:
            file_count: Number of files processed
            output_count: Number of output files generated
            
        Returns:
            Info message string
        """
        message = f"✓ Processed {file_count} file(s)\n"
        message += f"✓ Generated {output_count} output files\n\n"
        message += f"📁 Output Locations:\n"
        message += f"   Audio: {SWEAR_REMOVAL_AUDIO_OUTPUT_DIR}\n"
        message += f"   Transcripts: {SWEAR_REMOVAL_TRANSCRIPT_OUTPUT_DIR}\n"
        message += f"   Statistics: {SWEAR_REMOVAL_STATISTICS_OUTPUT_DIR}\n\n"
        
        # Docker tip
        if PlatformHelper.is_docker_environment():
            message += "💡 Tip: In Docker, access files via mounted volumes\n"
            message += "   Use the download links below or check your volume mappings"
        
        return message
    
    def remove_swears_from_files(
        self,
        files,
        swear_list_mode,
        custom_swear_file,
        edit_swears_text,
        censor_mode,
        beep_hertz,
        pad_pre,
        pad_post,
        output_format,
        reuse_transcript,
        progress=gr.Progress()
    ):
        """
        Remove swear words from uploaded audio files.
        
        Args:
            files: List of uploaded audio files
            swear_list_mode: Mode for swear list selection
            custom_swear_file: Custom swear list file (if uploaded)
            edit_swears_text: Edited swear list text
            censor_mode: "Mute" or "Beep"
            beep_hertz: Beep frequency in Hz
            pad_pre: Padding before censored word in ms
            pad_post: Padding after censored word in ms
            output_format: Output audio format
            reuse_transcript: If True, try to load existing transcript instead of re-transcribing
            progress: Gradio progress indicator
            
        Returns:
            Tuple of (status, audio, statistics, info, files)
        """
        if not files:
            return "Please upload audio files", None, "", "", None
        
        # Load swear list
        swears_dict = self._load_swear_list(
            swear_list_mode, custom_swear_file, edit_swears_text, progress
        )
        if isinstance(swears_dict, str):  # Error message
            return swears_dict, None, "", "", None
        
        logger.info(f"Loaded swear list with {len(swears_dict)} words")
        
        # Process files
        file_list = files if isinstance(files, list) else [files]
        results = []
        
        for i, file in enumerate(file_list):
            progress((i / len(file_list)) * 0.9, desc=f"Processing file {i+1}/{len(file_list)}...")
            
            try:
                result = self._process_single_file(
                    file, swears_dict, censor_mode, beep_hertz,
                    pad_pre, pad_post, output_format, reuse_transcript,
                    progress, i, len(file_list)
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process file: {e}", exc_info=True)
                results.append({'error': str(e)})
        
        progress(1.0, desc="Complete!")
        
        # Format results for UI
        return self._format_results(results)
    
    def _format_results(self, results):
        """
        Format processing results for UI display.
        
        Args:
            results: List of result dictionaries
            
        Returns:
            Tuple of (status, audio, statistics, info, files)
        """
        if not results:
            return "No files were processed", None, "", "No output files generated", None
        
        # Extract data from results
        all_output_files = []
        all_stats_text = ""
        
        for result in results:
            if 'error' in result:
                all_stats_text += f"\n\nError: {result['error']}"
                continue
            
            all_output_files.append(result['audio_path'])
            all_output_files.extend(result['stats_files'])
            
            all_stats_text += (
                f"\n\n{'='*60}\n"
                f"{result['base_name']}\n"
                f"{'='*60}\n"
                f"{result['report_text']}"
            )
        
        # Get first audio file for preview
        first_audio = next(
            (f for f in all_output_files 
             if f.endswith(('.mp3', '.wav', '.flac', '.m4a', '.m4b', '.aac', '.ogg', '.opus', '.ac3'))), 
            None
        )
        
        # Build info message
        transcript_info = self._build_info_message(len(results), len(all_output_files))
        
        return "Processing complete!", first_audio, all_stats_text, transcript_info, all_output_files
