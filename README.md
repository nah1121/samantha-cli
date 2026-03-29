# Samantha

**Give Claude a voice. Inspired by *Her*. Now 100% local and FREE!**

Samantha wraps the Claude CLI with speech recognition and text-to-speech. You speak, Claude thinks (with full Opus intelligence), and Samantha's voice responds. It's like having the AI from *Her* in your terminal.

She can do everything Claude Code can do — write code, create files, run commands, search the web — but you just talk to her instead of typing.

**NEW:** Samantha now runs completely offline with local AI models:
- 🎤 **Speech-to-Text:** OpenAI Whisper (local, free, private)
- 🔊 **Text-to-Speech:** Piper TTS (local, free, high-quality)
- 🚫 **No API costs, no internet required, 100% private**

---

## Quick Start

### 1. Install

```bash
# Clone the repository
git clone https://github.com/nah1121/samantha-cli.git
cd samantha-cli

# Install the package
pip install -e .

# Run the setup script (installs dependencies and downloads models)
samantha setup
```

That's it! No API keys, no cloud services, completely free.

### 2. Talk to Samantha

```bash
samantha  # Full voice mode - speak and hear responses
```

**First run:** Whisper and Piper models will download automatically (~200MB total). This takes a minute, then you're ready.

---

## Installation (Detailed)

### Prerequisites

- **Python 3.10+**
- **Claude CLI** installed → [claude.ai/download](https://claude.ai/download)
- **Claude Max or Pro subscription** (for the AI brain via `claude -p`)

### System Dependencies

**macOS:**
```bash
brew install portaudio ffmpeg
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt update
sudo apt install portaudio19-dev ffmpeg python3-dev
```

**Windows 11:**
1. Install [Microsoft Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. Install [FFmpeg](https://www.gyan.dev/ffmpeg/builds/) and add to PATH
3. PyAudio may need additional setup - see [PyAudio Windows Guide](https://people.csail.mit.edu/hubert/pyaudio/#downloads)

### Install Samantha

```bash
# 1. Clone and install
git clone https://github.com/nah1121/samantha-cli.git
cd samantha-cli
pip install -e .

# 2. Run automated setup (recommended)
samantha setup

# OR manually install dependencies
pip install faster-whisper piper-tts pyaudio numpy

# 3. Start talking
samantha
```

---

## How It Works

### Local Mode (Default - 100% Free)

```
Your voice → Whisper (local) → Claude CLI with Opus (your Max subscription)
                                      ↓
                          Claude response → Piper TTS (local) → Your speakers
```

- **Speech-to-Text:** Whisper (base model) runs on your CPU/GPU
- **Text-to-Speech:** Piper with high-quality Samantha voice
- **Brain:** Claude Opus via `claude -p` (full intelligence, tools, web access)
- **Cost:** $0 (only uses your Claude subscription)
- **Internet:** Not required after setup
- **Privacy:** Everything stays on your machine

### Cloud Mode (Legacy - Optional)

Still works if you prefer cloud services:
- **STT:** Google Speech Recognition (free, requires internet)
- **TTS:** Fish Audio (paid API, ~$1.25/hr of speech)

Switch modes anytime:
```bash
samantha config stt_engine cloud  # Use cloud STT
samantha config tts_engine cloud  # Use cloud TTS (needs API key)
```

---

## Commands

| Command | What it does |
|---|---|
| `samantha` | Start a voice conversation (local by default) |
| `samantha --text` | Text mode (type instead of speak, still hear voice) |
| `samantha --no-voice` | No TTS (speak to her, read her responses) |
| `samantha setup` | Run setup script (install deps, download models) |
| `samantha config` | Show current settings |
| `samantha config KEY VALUE` | Change a setting |
| `samantha resume` | Continue your last Claude session |

### During a conversation

- **Just talk naturally.** Samantha waits for you to finish before responding.
- **Say "goodbye"** or **"I'm done"** to end the session.
- **Say "start over"** or **"forget everything"** to clear history.
- **Press `Ctrl+C`** to exit immediately.

---

## Configuration

Settings are stored in `~/.samantha/config.yaml`.

### Key Settings

| Setting | Default | Description |
|---|---|---|
| `stt_engine` | `local` | Speech-to-text engine: `local` (whisper) or `cloud` (google) |
| `tts_engine` | `local` | Text-to-speech engine: `local` (piper) or `cloud` (fish) |
| `whisper_model` | `base` | Whisper model: `tiny`, `base`, `small`, `medium`, `large-v3` |
| `whisper_device` | `auto` | Device: `auto`, `cpu`, `cuda` (auto-detects GPU) |
| `piper_voice` | `samantha` | Voice: `samantha`, `amy`, `kathleen`, `ryan`, `libritts` |
| `speech_speed` | `0.95` | Playback speed (0.5 = slow, 2.0 = fast) |
| `language` | `en-US` | Speech recognition language |

### Examples

```bash
# View all settings
samantha config

# Use faster/smaller Whisper model (better for slower CPUs)
samantha config whisper_model tiny

# Use more accurate model (if you have GPU)
samantha config whisper_model small

# Speed up her voice
samantha config speech_speed 1.1

# Switch to cloud STT (requires internet)
samantha config stt_engine cloud

# Try different voice
samantha config piper_voice amy
```

---

## Model Information

### Whisper Models (STT)

| Model | Size | Speed | Accuracy | GPU Recommended |
|---|---|---|---|---|
| `tiny` | 39 MB | Fastest | Good | No |
| `base` | 74 MB | Fast | Better | No |
| `small` | 244 MB | Medium | Great | Optional |
| `medium` | 769 MB | Slow | Excellent | Yes |
| `large-v3` | 1550 MB | Slowest | Best | Yes |

**Default:** `base` (good balance for CPU usage)

Models download automatically on first use to `~/.cache/huggingface/`.

### Piper Voices (TTS)

| Voice | Description | Quality |
|---|---|---|
| `samantha` | Female (similar to Her) | High |
| `amy` | Female, clear | Medium |
| `kathleen` | Female, older | Low (faster) |
| `ryan` | Male | High |
| `libritts` | Multi-speaker | High |

Voice models download automatically to `~/.samantha/voices/`.

---

## Windows 11 Support

Samantha now has full Windows 11 support with proper audio handling:

1. **Install Visual C++ Build Tools** (required for PyAudio)
   - Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Select "Desktop development with C++"

2. **Install FFmpeg** (for audio playback)
   - Download: https://www.gyan.dev/ffmpeg/builds/
   - Extract and add `bin` folder to PATH

3. **Install Samantha:**
   ```powershell
   git clone https://github.com/nah1121/samantha-cli.git
   cd samantha-cli
   pip install -e .
   samantha setup
   ```

4. **Run:**
   ```powershell
   samantha
   ```

Audio playback uses PowerShell's built-in `Media.SoundPlayer` as the primary method, with FFmpeg as fallback.

---

## Performance Tips

### For Faster Response Times

1. **Use GPU if available:**
   ```bash
   samantha config whisper_device cuda
   ```

2. **Use smaller Whisper model:**
   ```bash
   samantha config whisper_model tiny  # Fastest
   ```

3. **Reduce phrase time limit** (stop listening sooner):
   ```bash
   samantha config phrase_time_limit 15
   ```

### For Better Accuracy

1. **Use larger Whisper model:**
   ```bash
   samantha config whisper_model small  # or medium with GPU
   ```

2. **Adjust microphone sensitivity** (lower = more sensitive):
   - Edit `~/.samantha/config.yaml`
   - The listen timeout and energy threshold are tuned automatically

---

## Troubleshooting

### "Local STT (Whisper) not available"

```bash
pip install faster-whisper pyaudio
```

On Windows, PyAudio may need: `pip install pipwin && pipwin install pyaudio`

### "Local TTS (Piper) not available"

```bash
pip install piper-tts
```

### "No audio player found"

- **macOS:** Should work out of the box (uses `afplay`)
- **Linux:** Install `ffmpeg` or `mpv`
- **Windows:** Install FFmpeg and add to PATH

### Microphone not working

1. Check system permissions (mic access)
2. Test with: `python -c "import pyaudio; pyaudio.PyAudio().get_default_input_device_info()"`
3. On Windows, make sure your mic is set as default device

### Models not downloading

Models download to:
- Whisper: `~/.cache/huggingface/`
- Piper: `~/.samantha/voices/`

Check internet connection and disk space (~500MB needed).

---

## Security & Privacy

Samantha runs Claude with `--dangerously-skip-permissions` so she can actually build things when you ask. This means Claude has full access to read/write files and run commands in your terminal.

**Local mode is 100% private:**
- All speech processing happens on your machine
- No data sent to cloud services (except Claude API for thinking)
- Conversation history stored locally at `~/.samantha/sessions/`
- Voice models cached locally, no tracking

**Best practices:**
- Run in directories where Claude can safely make changes
- Voice commands can be misheard — be aware near important files
- Use `--text` mode for sensitive work (see exactly what you're saying)

---

## Development

### Contributing

Some things that would make Samantha better:

- **Wake word** — "Hey Samantha" activation for background listening
- **Streaming TTS** — start speaking before full response is ready
- **More voices** — additional Piper voice models
- **Fine-tuned Whisper** — custom model for better accuracy
- **Web UI** — browser-based interface alongside CLI
- **Better Windows installer** — automated dependency setup

```bash
git clone https://github.com/nah1121/samantha-cli.git
cd samantha-cli
pip install -e .
```

### Project Structure

```
samantha/
├── cli.py          # Main CLI entry point
├── voice.py        # Voice engine (STT/TTS routing)
├── stt_local.py    # Local STT with Whisper
├── tts_local.py    # Local TTS with Piper
├── brain.py        # Claude integration
├── config.py       # Configuration management
├── personality.py  # Samantha's persona
└── ui.py           # Terminal interface
```

---

## License

MIT. See [LICENSE](LICENSE).

## Credits

- Inspired by *Her* (2013), directed by Spike Jonze
- Built with [Claude](https://claude.ai) by Anthropic
- Local STT powered by [OpenAI Whisper](https://github.com/openai/whisper) via [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- Local TTS powered by [Piper](https://github.com/rhasspy/piper)
- Terminal UI by [Rich](https://github.com/Textualize/rich)
- Legacy cloud TTS by [Fish Audio](https://fish.audio)

---

## FAQ

**Q: Do I need an Anthropic API key?**
A: No! Samantha uses `claude -p` which runs on your Claude Max/Pro subscription. Zero API cost.

**Q: Do I need a Fish Audio API key?**
A: No! The new local mode uses Piper TTS which is completely free. Fish Audio is now optional for those who prefer cloud TTS.

**Q: How much does it cost to run?**
A: $0 in local mode. Only your Claude subscription (which you already have).

**Q: Does it work offline?**
A: Yes! After initial setup and model downloads, everything runs locally except Claude API calls (which need internet).

**Q: Will it work on my old laptop?**
A: Yes! The `base` Whisper model works well on CPU. Use `tiny` for slower machines, or `small`/`medium` if you have a GPU.

**Q: Can I use my own voice?**
A: Not yet, but you can switch between Piper voices (`samantha`, `amy`, `kathleen`, `ryan`). Custom voice cloning is on the roadmap.

**Q: How is this different from ChatGPT Voice?**
A: Samantha has full access to your terminal and file system through Claude Code. She can write code, create files, run commands, and search the web — not just chat. Plus, she's 100% local and private.
