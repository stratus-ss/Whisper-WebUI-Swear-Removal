# Whisper-WebUI-Swear-Removal

> **Fork of [jhj0517/Whisper-WebUI](https://github.com/jhj0517/Whisper-WebUI)** with swear removal, subtitle merging, and Docker fixes

## Why This Fork Exists

This fork extends Whisper-WebUI with **profanity filtering** for audiobooks/spoken content and **subtitle quality improvements**. It adds swear word detection and censoring, intelligent subtitle segment merging, and Docker fixes not present upstream.

### Key Additions to Original Whisper-WebUI:

**Swear Removal**
- Dedicated tab for profanity filtering with mute or beep censoring
- Word-level timestamp precision with custom swear lists
- M4B audiobook format support
- SHA256-based transcript caching (10x-50x faster reprocessing)
- Censorship statistics and reporting

**Subtitle Quality**
- Intelligent segment merging — combines Whisper's over-segmented 1-3 word blocks into readable subtitles
- Respects punctuation boundaries and multilingual markers
- Tuned default parameters: reduced hallucination, better beam search, VAD enabled by default

**Docker**
- Fixed UVR (vocal remover) installation — upstream `setup.py` is broken, workaround applied
- Non-root container user with proper cache/config directory permissions
- Python 3.11-slim base image with CUDA 12.8 support

### Attribution
**Original Project**: [Whisper-WebUI](https://github.com/jhj0517/Whisper-WebUI) by [jhj0517](https://github.com/jhj0517)  
**License**: Maintains original project's licensing  
**All Core Features**: Full compatibility with upstream Whisper-WebUI functionality

---

A Gradio-based browser interface for [Whisper](https://github.com/openai/whisper). You can use it as an Easy Subtitle Generator **+ Profanity Filter**!

![screen](https://github.com/user-attachments/assets/caea3afd-a73c-40af-a347-8d57914b1d0f)

## Notebook
If you wish to try this on Colab, you can do it in [here](https://colab.research.google.com/github/stratus-ss/Whisper-WebUI-Swear-Removal/blob/master/notebook/whisper-webui.ipynb)!

# Feature
- Select the Whisper implementation you want to use between :
   - [openai/whisper](https://github.com/openai/whisper)
   - [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) (used by default)
   - [Vaibhavs10/insanely-fast-whisper](https://github.com/Vaibhavs10/insanely-fast-whisper)
- Generate subtitles from various sources, including :
  - Files
  - Youtube
  - Microphone
- Currently supported subtitle formats : 
  - SRT
  - WebVTT
  - txt ( only text file without timeline )
- Speech to Text Translation 
  - From other languages to English. ( This is Whisper's end-to-end speech-to-text translation feature )
- Text to Text Translation
  - Translate subtitle files using Facebook NLLB models
  - Translate subtitle files using DeepL API
- Pre-processing audio input with [Silero VAD](https://github.com/snakers4/silero-vad).
- Pre-processing audio input to separate BGM with [UVR](https://github.com/Anjok07/ultimatevocalremovergui). 
- Post-processing with speaker diarization using the [pyannote](https://huggingface.co/pyannote/speaker-diarization-3.1) model.
   - To download the pyannote model, you need to have a Huggingface token and manually accept their terms in the pages below.
      1. https://huggingface.co/pyannote/speaker-diarization-3.1
      2. https://huggingface.co/pyannote/segmentation-3.0

### Pipeline Diagram
![Transcription Pipeline](https://github.com/user-attachments/assets/1d8c63ac-72a4-4a0b-9db0-e03695dcf088)

# Installation and Running

- ## Running with Pinokio

⚠️ **Note**: This fork may not be available in Pinokio. For Pinokio installation, use the [original Whisper-WebUI](https://github.com/jhj0517/Whisper-WebUI) (without swear removal features).

The original app is able to run with [Pinokio](https://github.com/pinokiocomputer/pinokio).

1. Install [Pinokio Software](https://program.pinokio.computer/#/?id=install).
2. Open the software and search for Whisper-WebUI and install it.
3. Start the Whisper-WebUI and connect to the `http://localhost:7860`.

- ## Running with Docker 

1. Install and launch [Docker-Desktop](https://www.docker.com/products/docker-desktop/).

2. Git clone the repository

```sh
git clone https://github.com/stratus-ss/Whisper-WebUI-Swear-Removal.git
```

3. **(Optional) Configure speaker diarization**

   Copy the example env file and add your Hugging Face token:
   ```sh
   cp .env.example .env
   # Edit .env and set HF_TOKEN=hf_your_token_here
   ```
   You must also accept the model terms at [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1) and [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0).

4. Build the image ( Image is about 7GB~ )

```sh
docker compose build 
```

5. Run the container 

```sh
docker compose up
```

6. Connect to the WebUI with your browser at `http://localhost:7860`

If needed, update the [`docker-compose.yaml`](https://github.com/stratus-ss/Whisper-WebUI-Swear-Removal/blob/master/docker-compose.yaml) to match your environment.

- ## Run Locally

### Prerequisite
To run this WebUI, you need to have `git`, `3.10 <= python <= 3.12`, `FFmpeg`.

**Edit `--extra-index-url` in the [`requirements.txt`](https://github.com/stratus-ss/Whisper-WebUI-Swear-Removal/blob/master/requirements.txt) to match your device.<br>**
By default, the WebUI assumes you're using an Nvidia GPU and **CUDA 12.8.** If you're using Intel or another CUDA version, read the [`requirements.txt`](https://github.com/stratus-ss/Whisper-WebUI-Swear-Removal/blob/master/requirements.txt) and edit `--extra-index-url`.

Please follow the links below to install the necessary software:
- git : [https://git-scm.com/downloads](https://git-scm.com/downloads)
- python : [https://www.python.org/downloads/](https://www.python.org/downloads/) **`3.10 ~ 3.12` is recommended.** 
- FFmpeg :  [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
- CUDA : [https://developer.nvidia.com/cuda-downloads](https://developer.nvidia.com/cuda-downloads)

After installing FFmpeg, **make sure to add the `FFmpeg/bin` folder to your system PATH!**

### Installation Using the Script Files

1. git clone this repository
```shell
git clone https://github.com/stratus-ss/Whisper-WebUI-Swear-Removal.git
```
2. Run `install.bat` or `install.sh` to install dependencies. (It will create a `venv` directory and install dependencies there.)
3. Start WebUI with `start-webui.bat` or `start-webui.sh` (It will run `python app.py` after activating the venv)

And you can also run the project with command line arguments if you like to, see [wiki](https://github.com/jhj0517/Whisper-WebUI/wiki/Command-Line-Arguments) for a guide to arguments.

# VRAM Usages
This project is integrated with [faster-whisper](https://github.com/guillaumekln/faster-whisper) by default for better VRAM usage and transcription speed.

According to faster-whisper, the efficiency of the optimized whisper model is as follows: 
| Implementation    | Precision | Beam size | Time  | Max. GPU memory | Max. CPU memory |
|-------------------|-----------|-----------|-------|-----------------|-----------------|
| openai/whisper    | fp16      | 5         | 4m30s | 11325MB         | 9439MB          |
| faster-whisper    | fp16      | 5         | 54s   | 4755MB          | 3244MB          |

If you want to use an implementation other than faster-whisper, use `--whisper_type` arg and the repository name.<br>
Read [wiki](https://github.com/jhj0517/Whisper-WebUI/wiki/Command-Line-Arguments) for more info about CLI args.

If you want to use a fine-tuned model, manually place the models in `models/Whisper/` corresponding to the implementation.

Alternatively, if you enter the huggingface repo id (e.g, [deepdml/faster-whisper-large-v3-turbo-ct2](https://huggingface.co/deepdml/faster-whisper-large-v3-turbo-ct2)) in the "Model" dropdown, it will be automatically downloaded in the directory.

![image](https://github.com/user-attachments/assets/76487a46-b0a5-4154-b735-ded73b2d83d4)

# REST API
If you're interested in deploying this app as a REST API, please check out [/backend](https://github.com/stratus-ss/Whisper-WebUI-Swear-Removal/tree/master/backend).

## TODO🗓

- [x] Add DeepL API translation
- [x] Add NLLB Model translation
- [x] Integrate with faster-whisper
- [x] Integrate with insanely-fast-whisper
- [x] Integrate with whisperX ( Only speaker diarization part )
- [x] Add background music separation pre-processing with [UVR](https://github.com/Anjok07/ultimatevocalremovergui)  
- [x] Add fast api script
- [ ] Add CLI usages
- [ ] Support real-time transcription for microphone

### Translation 🌐
Any PRs that translate the language into [translation.yaml](https://github.com/stratus-ss/Whisper-WebUI-Swear-Removal/blob/master/configs/translation.yaml) would be greatly appreciated!

---

## Attribution & Upstream

This fork is based on **[Whisper-WebUI](https://github.com/jhj0517/Whisper-WebUI)** by **[jhj0517](https://github.com/jhj0517)**. All credit for core transcription, Gradio UI, translation, diarization, and REST API goes to the original project. Fork contributions (swear removal, segment merging, Docker fixes) by **[stratus-ss](https://github.com/stratus-ss)**.

For maintenance details and upstream merge instructions, see [FORK_MAINTENANCE.md](FORK_MAINTENANCE.md).

**Issues**: [General/transcription](https://github.com/jhj0517/Whisper-WebUI/issues) | [Swear removal/fork-specific](https://github.com/stratus-ss/Whisper-WebUI-Swear-Removal/issues)  
**Support the original developer**: [Star](https://github.com/jhj0517/Whisper-WebUI) or [Sponsor](https://github.com/sponsors/jhj0517) jhj0517
