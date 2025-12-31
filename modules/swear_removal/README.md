# Swear Removal Module

This module provides profanity censoring for audio and video files, integrated with Whisper-WebUI.

## Features

- **Multiple Censoring Modes**: Mute (silence) or beep profanity
- **Flexible Swear Lists**: Default (734 words), custom upload, or in-browser editing
- **Transcript Preservation**: Saves transcripts in monkeyplug-compatible format
- **Transcript Reuse**: Skip re-transcription for 10x-50x faster re-processing
- **Detailed Statistics**: Word frequency, timeline, duration analysis
- **Multiple Formats**: Supports mp3, wav, flac, m4a, and more

## Architecture

```
SwearListManager → AudioCleaner → CensorshipStatistics
       ↓                 ↓                 ↓
  Load Lists      Clean Audio       Generate Stats
```

### Components

#### `swear_manager.py` - SwearListManager
Manages swear word lists:
- Loads default list (734 words from monkeyplug)
- Loads custom lists (text or JSON format)
- Normalizes words for matching (case-insensitive, no punctuation)
- Caches loaded lists for performance

#### `audio_cleaner.py` - AudioCleaner
Cleans audio files:
- Identifies profane words from transcription
- Creates FFmpeg filter chains (mute or beep)
- Processes audio with configurable padding
- **NEW**: Saves/loads transcripts for reuse
- Supports multiple output formats

#### `statistics.py` - CensorshipStatistics
Generates reports:
- Total words vs censored words
- Censorship percentage
- Word frequency analysis
- Timeline with timestamps
- Duration statistics

## Transcript Reuse

### Why Use Transcript Reuse?

Transcription is the slowest part of the process. For large audiobooks:
- Transcription: 10-60 minutes (depends on file size and GPU)
- Audio cleaning: 1-5 minutes (FFmpeg is fast)

**With transcript reuse**, you only transcribe once, then can:
- Try different censoring modes (mute vs beep)
- Adjust padding values
- Test different swear lists
- Change output formats

All in **seconds** instead of **minutes/hours**!

### Transcript Format

Saved as JSON in monkeyplug-compatible format:

```json
[
  {
    "word": "string",     // The word as transcribed
    "start": 0.0,         // Start time in seconds
    "end": 0.5,           // End time in seconds
    "conf": 0.95,         // Confidence score (0.0-1.0)
    "scrub": false        // Whether word should be censored
  }
]
```

### File Naming

Transcripts are automatically named:
- Format: `{original_filename}_transcript_{timestamp}.json`
- Example: `audiobook_ch1_transcript_20251229_143022.json`

When reuse is enabled, the system finds the most recent transcript matching the filename.

### Storage Location

Transcripts are stored in:
```
outputs/swear_removal/transcripts/
```

This directory is automatically created and managed.

## Usage Examples

### Example 1: Basic Usage

```python
from modules.swear_removal.swear_manager import SwearListManager
from modules.swear_removal.audio_cleaner import AudioCleaner

# Load default swear list
manager = SwearListManager()
swears = manager.load_default_list()

# Clean audio
cleaner = AudioCleaner()
output_path, censored_words = cleaner.clean_audio(
    input_path="input.mp3",
    output_path="output.mp3",
    word_list=transcribed_words,  # From Whisper
    swears_dict=swears,
    beep=False,
    transcript_path="output_transcript.json"  # Save for reuse
)

print(f"Censored {len(censored_words)} words")
```

### Example 2: Reusing Transcript

```python
# Load existing transcript (skip re-transcription)
word_list = cleaner.load_transcript_from_file("output_transcript.json")

if word_list:
    # Process with different parameters
    output_path, censored_words = cleaner.clean_audio(
        input_path="input.mp3",
        output_path="output_beep.mp3",
        word_list=word_list,  # Reused!
        swears_dict=swears,
        beep=True,  # Try beep mode this time
        beep_hertz=1200
    )
```

### Example 3: Custom Swear List

```python
# Upload custom list
swears = manager.load_custom_list("my_swears.txt", "my_list")

# Or create from list
words = ["word1", "word2", "word3"]
manager.save_custom_list(words, "my_swears.json", format="json")
```

### Example 4: Generate Statistics

```python
from modules.swear_removal.statistics import CensorshipStatistics

stats = CensorshipStatistics()
analysis = stats.analyze_results(word_list, censored_words, audio_duration)

# Text report
print(stats.generate_report(analysis))

# JSON report
json_report = stats.generate_json_report(analysis)
```

## Configuration

In `backend/configs/config.yaml`:

```yaml
swear_removal:
  default_swear_list: "default"
  cache_ttl: 3600                # 1 hour
  max_file_size_mb: 500
  supported_formats: ["mp3", "wav", "flac", "m4a", "aac", "ogg", "opus", "mp4", "avi", "mkv"]
```

## API Endpoints

### Remove Swears
```
POST /swear-removal/
```
Upload audio file and process with parameters.

### List Swear Lists
```
GET /swear-removal/swear-lists
```
Get available swear lists.

### Upload Custom List
```
POST /swear-removal/swear-lists/upload
```
Upload custom swear list file.

### Get Swear List
```
GET /swear-removal/swear-lists/{list_id}
```
Retrieve contents of specific list.

## Dependencies

- `monkeyplug`: FFmpeg filter generation logic
- `mmguero`: Utility functions
- `mutagen`: Audio metadata handling
- `soundfile`: Audio I/O
- `ffmpeg`: Audio processing (system dependency)

## Testing

Run module tests:
```bash
python tests/test_swear_removal.py
```

All tests validate:
- Swear list loading/parsing
- Word identification
- Transcript save/load
- Filter generation
- Statistics calculation

## Performance

| Operation | Time (1-hour audiobook) |
|-----------|------------------------|
| First run (with transcription) | ~20-40 minutes |
| Subsequent runs (transcript reuse) | ~2-3 minutes |
| **Speed improvement** | **10x-20x faster!** |

## Compatibility

### Monkeyplug Integration

Our transcript format is **fully compatible** with monkeyplug CLI:

```bash
# Process with Whisper-WebUI, get transcript
# Then use with monkeyplug CLI:
monkeyplug.py --input-transcript audiobook_transcript.json \
              -i audiobook.mp3 \
              -o audiobook_clean.mp3
```

### Output Formats

All monkeyplug output formats supported:
- Audio: mp3, wav, flac, m4a, aac, ogg, opus, ac3
- Video: mp4, avi, mkv (audio stream replacement)

## Troubleshooting

### Transcript Not Found
If "Reuse transcript" is enabled but transcript isn't found:
- The system will automatically transcribe
- Check `outputs/swear_removal/transcripts/` directory
- Ensure filename matches original file

### No Words Censored
If no profanity is detected:
- Check that swear list contains the words you expect
- Try "Edit Default List" to see what's in the list
- Upload custom list if needed

### FFmpeg Errors
If audio cleaning fails:
- Ensure ffmpeg is installed: `ffmpeg -version`
- Check output format is supported
- Try "MATCH" format to use input format

## Future Enhancements

Potential additions:
- [ ] Transcript format converter (SRT/VTT to monkeyplug format)
- [ ] Batch processing with shared transcript cache
- [ ] Swear list editor with categories (mild/moderate/severe)
- [ ] Export censorship timeline as SRT/VTT subtitles
- [ ] Support for alternative words (replace instead of censor)
- [ ] Machine learning-based profanity detection
