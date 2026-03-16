# Samantha

**Give Claude a voice. Inspired by *Her*.**

Samantha wraps the Claude CLI with speech recognition and text-to-speech. You speak, Claude thinks (with full Opus intelligence), and Samantha's voice responds. It's like having the AI from *Her* in your terminal.

She can do everything Claude Code can do — write code, create files, run commands, search the web — but you just talk to her instead of typing.

---

## Install

The easiest way: open Claude Code in your terminal and say:

> "Install Samantha for me from this repo"

Claude will read the CLAUDE.md and walk you through everything.

Or do it manually:

```bash
# 1. Install system dependency (needed for microphone)
brew install portaudio          # macOS
# sudo apt install portaudio19-dev  # Linux

# 2. Clone and install
git clone https://github.com/ethanplusai/samantha-cli.git
cd samantha-cli
pip install -e .

# 3. Set your Fish Audio API key (for Samantha's voice)
#    Get one free at https://fish.audio/app/api-keys
export FISH_API_KEY=your_key_here
#    Or save it permanently:
samantha config fish_api_key your_key_here

# 4. Talk to her
samantha
```

**That's it.** No Anthropic API key needed — Samantha uses `claude -p` which runs on your existing Claude Max/Pro subscription. Zero API cost for the AI. Fish Audio TTS is the only paid service (~$1.25/hr of speech).

---

## Commands

| Command | What it does |
|---|---|
| `samantha` | Start a voice conversation |
| `samantha --text` | Text mode (type instead of speak, still hear her voice) |
| `samantha --no-voice` | No TTS (speak to her, read her responses) |
| `samantha --text --no-voice` | Pure text mode, no audio at all |
| `samantha resume` | Continue your last Claude session with voice |
| `samantha resume SESSION_ID` | Resume a specific Claude session |
| `samantha config` | Show current settings |
| `samantha config KEY VALUE` | Set a config value |

### During a conversation

- **Just talk naturally.** Samantha waits for you to finish before responding.
- **Say "goodbye"** or **"I'm done"** to end the session.
- **Say "start over"** or **"forget everything"** to clear conversation history.
- **Press `Ctrl+C`** to exit immediately.

---

## How It Works

```
Your voice → Google STT (free) → Claude CLI with Opus (your Max subscription)
                                          ↓
                              Haiku summarizes for voice (if response is long)
                                          ↓
                              Fish Audio TTS (Samantha's voice) → Your speakers
```

- **Brain:** Claude Opus via `claude -p` (full intelligence, tools, file access, web search)
- **Voice summary:** Claude Haiku condenses long responses into 2-3 spoken sentences
- **Voice:** Fish Audio with a voice model inspired by *Her* (2013)
- **Speech recognition:** Google's free STT service
- **History:** Conversations saved locally at `~/.samantha/sessions/`

Samantha has full access to Claude's tools — she can create files, edit code, run terminal commands, and search the web. When she does complex work, you'll see Opus's full output in your terminal, then hear a spoken summary.

---

## Configuration

Settings are stored in `~/.samantha/config.yaml`.

| Setting | Default | What it does |
|---|---|---|
| `fish_api_key` | — | Your Fish Audio API key (required for voice) |
| `speech_speed` | `0.95` | How fast she talks (0.5 = slow, 2.0 = fast) |
| `language` | `en-US` | Speech recognition language |
| `max_history` | `10` | How many exchanges she remembers |

```bash
# Examples
samantha config fish_api_key sk-abc123       # Set API key
samantha config speech_speed 1.1             # Speed up her voice
samantha config max_history 20               # Remember more
```

---

## Security

Samantha runs Claude with `--dangerously-skip-permissions` so she can actually build things when you ask. This means Claude has full access to read/write files and run commands in your terminal.

- Run Samantha in directories where you're okay with Claude making changes
- Voice commands can be misheard — be aware when working near important files
- All conversation history stays local on your machine

---

## Requirements

- **Python 3.10+**
- **Claude CLI** installed and authenticated → [docs.anthropic.com](https://docs.anthropic.com/en/docs/claude-cli)
- **Claude Max or Pro subscription** (Samantha uses `claude -p`, no API key needed)
- **Fish Audio API key** → [fish.audio](https://fish.audio/app/api-keys) (for her voice)
- **Microphone** (or use `--text` mode)

---

## Contributing

Some things that would make Samantha better:

- **Wake word** — "Hey Samantha" activation so she listens in the background
- **Streaming TTS** — start speaking before the full response is ready
- **Local STT** — Whisper for offline/private use
- **Better voice** — exploring ElevenLabs, Cartesia, or local models
- **Web UI** — browser-based interface alongside the CLI

```bash
git clone https://github.com/ethanplusai/samantha-cli.git
cd samantha-cli
pip install -e .
```

---

## License

MIT. See [LICENSE](LICENSE).

## Credits

- Inspired by *Her* (2013), directed by Spike Jonze
- Built with [Claude](https://claude.ai) by Anthropic
- Voice powered by [Fish Audio](https://fish.audio)
- Terminal UI by [Rich](https://github.com/Textualize/rich)
