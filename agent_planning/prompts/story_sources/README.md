# Story Sources — Episode Transcripts for Story Context

Transcripts of sitcom episodes used as **reference material** for
generating the Edificio Nexo / Plomeros Digitales Spanish sitcom stories
(see `../story_template.md` and `../story_config_nexo_libro1.md`). The
template explicitly lists the inspiration set:

> Inspired by: Big Bang Theory (character-driven socially-awkward genius
> humor), Better Off Ted (absurdist workplace comedy, deadpan),
> Avenue 5, Eureka (quirky community solving ordinary problems
> extraordinarily). The IT Crowd is a tonal reference for the workplace
> dynamics.

The transcripts in `srt/` capture the actual scene-by-scene language,
jokes, and timing that the writer can mine for tone and beats.

## Layout

```
story_sources/
├── srt/                # generated SRTs land here (one per episode)
├── scripts/
│   ├── extract_audio.sh   # ffmpeg wrapper — video → MP3 for STT
│   └── stt_uploader.py    # Whisper-WebUI client — MP3 → SRT
└── README.md
```

## Current batch — running now

A daemon was launched on stratus-nas against `/tmp/forTTS`:

- **Inputs:**  27 sitcom episodes encoded to MP3
  (BBT × 7, Better Off Ted × 7, IT Crowd × 6, Eureka × 7). The IT Crowd
  Series Finale ("The Internet Is Coming") was not present in the source
  library.
- **Settings:** `large-v3` model, English, VAD on, word timestamps.
  Tweak via `--config` if `lang` or model needs to change.
- **DAEMON PID:** see `/tmp/forTTS/.stt_uploader.pid` on stratus-nas.
- **LOG:** `/tmp/forTTS/.stt_uploader.log` on stratus-nas.
- **OUTPUTS:** SRTs to `/tmp/forTTS/srt/`; move or copy them to
  `./srt/` (this directory) when the batch completes.
- **STOP:** `ssh stratus@stratus-nas 'kill $(cat /tmp/forTTS/.stt_uploader.pid)'`

## End-to-end workflow (for the next batch)

1. Drop video files into a working dir (e.g. `/tmp/forTTS`).
2. **Extract MP3s** in parallel:
   ```bash
   ./scripts/extract_audio.sh /tmp/forTTS
   ```
   Default settings: mono, 16 kHz, libmp3lame q:a 4 — ideal for STT.
3. **Run the STT uploader** in `--watch` mode in the background:
   ```bash
   nohup python3 ./scripts/stt_uploader.py --watch --source /tmp/forTTS \
       --config /path/to/config.yaml >/dev/null 2>&1 &
   ```
   The script auto-discovers `*.mp3`, uploads each, polls `/task/{id}`,
   writes the SRT to `<source>/srt/`, and moves the MP3 to `<source>/done/`.
4. **Copy the SRTs** to `./srt/` here so they live next to the story
   config.

For one-off transcription without watching: `python3
./scripts/stt_uploader.py --once --source /tmp/forTTS`.

## Configuration

`stt_uploader.py` uses the same YAML schema as
`/home/stratus/git_projects/download_ANS/local_whisper/`. Example block
(see the existing `config.yaml` next to that script):

```yaml
whisper:
  host: "whisper.x86experts.com"
  port: 8001
  lang: "english"
  model_size: "large-v3"
  vad_filter: true
  word_timestamps: true
  compute_type: "float16"
  beam_size: 5
  best_of: 5
  batch_size: 8
```

## Notes / gotchas

- The reference implementation at `download_ANS/` has an SRT-audit and
  retry pass for hallucination loops. This version does **not** include
  audit — the goal here is clean transcript text, not hallucination
  filtering. If retry logic is needed, copy
  `download_ANS/srt_audit.py` alongside.
- `stt_uploader.py` writes a `.uploading` sidecar while a file is in
  flight to prevent double-pickup in `--watch` mode. Stale `.uploading`
  files are cleaned on startup.
- The daemon stays alive across SSH sessions (`nohup` + `disown`).
  Use `kill $(cat .stt_uploader.pid)` to stop.
