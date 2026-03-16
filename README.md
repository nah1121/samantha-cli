# Samantha

**Give Claude a voice. Inspired by *Her*.**

Samantha is a terminal-based voice assistant that wraps the Claude CLI with speech recognition and text-to-speech. You speak, Claude thinks, and Samantha's voice responds. It's like having the AI from *Her* in your terminal.

<!-- screenshot / demo gif placeholder -->
<!-- ![Samantha demo](docs/demo.gif) -->

---

## Quick Start

```bash
pip install samantha-cli
samantha
```

That's it. Speak into your mic, and Samantha responds.

## Requirements

- **Python 3.10+**
- **Claude CLI** installed and authenticated (`claude` on your PATH). Get it at [docs.anthropic.com](https://docs.anthropic.com/en/docs/claude-cli).
- **Fish Audio API key** (for voice output). Sign up at [fish.audio](https://fish.audio) and grab your key.
- **Microphone** (for voice input). Or use `--text` mode if you prefer typing.

### System Dependencies

On macOS:
```bash
brew install portaudio
```

On Ubuntu/Debian:
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
```

## Setup

### 1. Install

```bash
pip install samantha-cli
```

Or install from source:

```bash
git clone https://github.com/ethanplusai/samantha-cli.git
cd samantha-cli
pip install -e .
```

### 2. Configure your Fish Audio API key

```bash
samantha config fish_api_key YOUR_KEY_HERE
```

Or set it as an environment variable:

```bash
export FISH_API_KEY=your_key_here
```

### 3. Run

```bash
samantha
```

## Usage

### Voice Mode (default)

```bash
samantha
```

Speak naturally. Samantha listens, thinks, and responds with voice. Press `Ctrl+C` to exit, or say "goodbye."

### Text Mode

```bash
samantha --text
```

Type your messages instead of speaking. Samantha still responds with voice if configured.

### Silent Mode

```bash
samantha --text --no-voice
```

Pure text conversation, no audio in or out.

### Configuration

```bash
samantha config                        # Show all settings
samantha config fish_api_key           # Show one setting
samantha config fish_api_key sk-xxx    # Set a value
samantha config speech_speed 1.1       # Adjust voice speed
```

All settings are stored in `~/.samantha/config.yaml`.

| Setting | Default | Description |
|---|---|---|
| `fish_api_key` | (none) | Fish Audio API key for TTS |
| `voice_model_id` | `474887f7...` | Fish Audio voice model ID |
| `speech_speed` | `0.95` | TTS speed (0.5 - 2.0) |
| `language` | `en-US` | Speech recognition language |
| `max_history` | `10` | Conversation turns to remember |
| `listen_timeout` | `10` | Seconds to wait for speech |
| `phrase_time_limit` | `30` | Max seconds per utterance |

## How It Works

```
Microphone
    |
    v
SpeechRecognition (Google free STT)
    |
    v
claude -p (Claude CLI, headless mode)
    |
    v
Fish Audio TTS (Samantha voice)
    |
    v
Speaker
```

Samantha uses Claude Max through the official CLI in headless mode (`claude -p`), so there are no API costs. Speech recognition uses Google's free STT service. Text-to-speech uses Fish Audio with a voice model tuned to sound warm and natural.

The personality is baked into the system prompt: warm, curious, concise. Responses are kept to 2-3 sentences because she's speaking, not writing.

## Project Structure

```
samantha-cli/
  samantha/
    __init__.py       # Version
    cli.py            # Click CLI entry point + main loop
    voice.py          # Mic input (STT) + speaker output (TTS)
    brain.py          # Claude CLI integration
    config.py         # ~/.samantha/config.yaml management
    personality.py    # System prompt / persona
    ui.py             # Rich terminal display
  pyproject.toml
  LICENSE
  README.md
```

## Contributing

Contributions are welcome. Some ideas:

- **Wake word detection** -- "Hey Samantha" activation
- **Streaming TTS** -- start speaking before the full response is ready
- **Local STT** -- Whisper instead of Google for offline use
- **Voice activity detection** -- smarter silence handling
- **Conversation export** -- save transcripts to markdown

```bash
git clone https://github.com/ethanplusai/samantha-cli.git
cd samantha-cli
pip install -e ".[dev]"
```

## License

MIT. See [LICENSE](LICENSE).

## Credits

- Inspired by *Her* (2013), directed by Spike Jonze
- Built with [Claude](https://claude.ai) by Anthropic
- Voice powered by [Fish Audio](https://fish.audio)
- Terminal UI by [Rich](https://github.com/Textualize/rich)
