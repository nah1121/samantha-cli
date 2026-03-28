# Samantha CLI

## What This Is
A voice wrapper around Claude Code that runs **100% locally and FREE**. You speak, Claude thinks, Samantha's voice responds. Same Claude brain, same tools, same Max subscription - but now with fully local, private speech-to-text and text-to-speech. No API costs, no cloud dependencies.

## NEW: Local & Free Mode
- **Speech-to-Text:** OpenAI Whisper (runs on your CPU/GPU, completely free)
- **Text-to-Speech:** Piper TTS (high-quality local synthesis, completely free)
- **No API keys needed** (except Claude, which uses your Max subscription)
- **100% private** - all voice processing stays on your machine
- **Works offline** after initial model downloads

## Setup

### Quick Start
```bash
# 1. Install the package
git clone https://github.com/nah1121/samantha-cli.git
cd samantha-cli
pip install -e .

# 2. Run automated setup (installs everything)
samantha setup

# 3. Start talking
samantha
```

### Manual Setup (if needed)

1. **Check Claude CLI is installed**: Run `which claude`. If not found → install from https://claude.ai/download

2. **Check Python**: Need Python 3.10+. Run `python3 --version`.

3. **Install system dependencies:**
   - **macOS:** `brew install portaudio ffmpeg`
   - **Linux:** `sudo apt install portaudio19-dev ffmpeg python3-dev`
   - **Windows:** Install Visual C++ Build Tools + FFmpeg (see README.md for details)

4. **Install Python packages:**
   ```bash
   pip install faster-whisper piper-tts pyaudio numpy rich click pyyaml
   ```

5. **Test it:**
   ```bash
   samantha --text  # Text mode first to verify Claude + TTS works
   samantha         # Full voice mode
   ```

## How to Check if Already Set Up
- Run `samantha config` — shows current config
- If `stt_engine: local` and `tts_engine: local` → you're in free mode ✓
- Config file lives at `~/.samantha/config.yaml`
- **NO API keys needed** for local mode

## How It Works (Local Mode)
```
Your voice → Whisper (local, free) → claude -p (Claude Max) → Piper TTS (local, free) → Your speakers
```

- `samantha/cli.py` — Main entry point, Click CLI
- `samantha/voice.py` — Voice engine router (local/cloud selection)
- `samantha/stt_local.py` — Local STT using faster-whisper
- `samantha/tts_local.py` — Local TTS using Piper
- `samantha/brain.py` — Wraps `claude -p` subprocess, builds prompts with personality
- `samantha/personality.py` — The Samantha persona prompt
- `samantha/config.py` — Manages `~/.samantha/config.yaml`
- `samantha/ui.py` — Rich terminal display with colored status indicators

## Key Details

### Local Mode (Default)
- **STT:** Whisper `base` model (CPU-friendly, ~140MB)
- **TTS:** Piper with `samantha` voice (Her-inspired, ~60MB)
- **Device:** Auto-detects CUDA if available, falls back to CPU
- **Cost:** $0 (only uses your Claude subscription)
- **Privacy:** Everything stays on your machine

### Cloud Mode (Legacy, Optional)
- **STT:** Google Speech Recognition (free, requires internet)
- **TTS:** Fish Audio (~$1.25/hr of speech, requires API key)

Switch anytime:
```bash
samantha config stt_engine cloud  # or local
samantha config tts_engine cloud  # or local
```

### Models
- **Whisper models:** `tiny`, `base`, `small`, `medium`, `large-v3` (configurable)
- **Piper voices:** `samantha`, `amy`, `kathleen`, `ryan`, `libritts`
- Claude is called via `claude -p` with stdin, uses the user's Max subscription
- Conversation history maintained in memory (last 10 exchanges)
- Phrase time limit: 30 seconds (configurable)

## Commands
- `samantha` — Full voice mode (speak + hear) - 100% local by default
- `samantha --text` — Text only (type + hear)
- `samantha --no-voice` — Voice input, text output (speak + read)
- `samantha config` — View/set configuration
- `samantha setup` — Run setup script (install deps, download models)

## Configuration Examples
```bash
# View current setup
samantha config

# Use smaller/faster Whisper model (for slower CPUs)
samantha config whisper_model tiny

# Use more accurate model (if you have GPU)
samantha config whisper_model small
samantha config whisper_device cuda

# Try different voice
samantha config piper_voice amy

# Switch to cloud mode (requires internet + API keys)
samantha config stt_engine cloud
samantha config tts_engine cloud
```

## Windows 11 Support
Samantha now has full Windows 11 compatibility:

1. **Prerequisites:**
   - Visual C++ Build Tools (for PyAudio)
   - FFmpeg (for audio playback)
   - Python 3.10+

2. **Audio handling:**
   - Primary: PowerShell's `Media.SoundPlayer` (built-in)
   - Fallback: FFmpeg (if installed)
   - Microphone: PyAudio with proper device detection

3. **Installation:**
   ```powershell
   pip install -e .
   samantha setup  # Handles Windows-specific setup
   ```

See README.md for detailed Windows installation instructions.

## Troubleshooting

### "Local STT (Whisper) not available"
```bash
pip install faster-whisper pyaudio
```
Windows: May need `pip install pipwin && pipwin install pyaudio`

### "Local TTS (Piper) not available"
```bash
pip install piper-tts
```

### Microphone not working
1. Check system permissions (mic access)
2. On Windows, ensure mic is set as default device
3. Test: `python -c "import pyaudio; pyaudio.PyAudio().get_default_input_device_info()"`

### Models not downloading
- Whisper models: Download to `~/.cache/huggingface/` (automatic)
- Piper voices: Download to `~/.samantha/voices/` (automatic)
- Need internet connection for first-time download (~200MB total)

### Performance issues
- Use smaller model: `samantha config whisper_model tiny`
- Enable GPU: `samantha config whisper_device cuda`
- Reduce phrase limit: `samantha config phrase_time_limit 15`

## What's Different from Cloud Version
| Feature | Local (New) | Cloud (Legacy) |
|---|---|---|
| **STT** | Whisper (free, offline) | Google (free, online) |
| **TTS** | Piper (free, offline) | Fish Audio (paid, online) |
| **Cost** | $0 | ~$1.25/hr speech |
| **Internet** | Only for Claude API | Required for STT & TTS |
| **Privacy** | 100% local processing | Data sent to cloud |
| **Setup** | Model downloads (~200MB) | API key required |
| **Quality** | High (configurable models) | High |
| **Speed** | Fast (CPU/GPU, depends on model) | Fast (depends on network) |

## Performance Tuning

### For Speed (slower machines)
```bash
samantha config whisper_model tiny     # Fastest, smallest
samantha config whisper_device cpu     # Explicit CPU
samantha config phrase_time_limit 15   # Stop listening sooner
```

### For Accuracy (powerful machines)
```bash
samantha config whisper_model small    # Better accuracy
samantha config whisper_device cuda    # Use GPU
samantha config phrase_time_limit 30   # Listen longer
```

## Privacy & Security
- **Local mode:** All voice data processed on your machine, never sent to cloud (except Claude API calls)
- **Conversation history:** Stored locally at `~/.samantha/sessions/`
- **Models:** Cached locally, no tracking or telemetry
- **Claude access:** Runs with `--dangerously-skip-permissions` for full tool access
- **Best practice:** Use in directories where Claude can safely make changes

## Summary for Users
When helping users install Samantha, emphasize:

1. **It's now completely free** - No Fish Audio API key needed
2. **100% private** - All voice processing stays on their machine
3. **Easy setup** - Just run `samantha setup` and it handles everything
4. **Works offline** - After model downloads, no internet required (except Claude)
5. **Fast & high-quality** - Whisper and Piper are production-grade models
6. **Windows compatible** - Full Windows 11 support with proper audio handling

The old cloud mode still works if users prefer it, but local mode is now the default and recommended setup.
