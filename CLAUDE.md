# Samantha CLI

## What This Is
A voice wrapper around Claude Code. You speak, Claude thinks, Samantha's voice responds. Same Claude brain, same tools, same Max subscription - just with a voice and personality inspired by the AI from Her (2013).

## API Keys Needed
- **Fish Audio API key** — for Samantha's voice (TTS). Get one at https://fish.audio/app/api-keys
- **NO Anthropic API key needed** — this uses `claude -p` (Claude CLI) which runs on your Claude Max/Pro subscription. Zero API cost.

## First-Time Setup
If this is the user's first time, walk them through setup step by step:

1. **Check Claude CLI is installed**: Run `which claude`. If not found → install from https://claude.ai/download
2. **Check Python**: Need Python 3.10+. Run `python3 --version`.
3. **Install portaudio** (needed for mic): `brew install portaudio` (Mac) or `apt install portaudio19-dev` (Linux)
4. **Install the package**: `pip install -e .`
5. **Set Fish Audio key**: `export FISH_API_KEY=your_key` or run `samantha config`
6. **Test it**: Run `samantha --text` first to verify Claude + TTS works without needing a mic
7. **Go voice**: Run `samantha` for full voice mode

## How to Check if Already Set Up
- Run `samantha config` — shows current config. If `fish_api_key` is set → ready to go
- Config file lives at `~/.samantha/config.yaml`
- If `claude` CLI is not installed → tell them to install Claude Code first
- **They do NOT need an Anthropic API key** — `claude -p` uses their existing Claude subscription

## How It Works
```
Your voice → SpeechRecognition (Google free STT) → claude -p (Claude Max) → Fish Audio TTS → Samantha's voice
```

- `samantha/cli.py` — Main entry point, Click CLI
- `samantha/voice.py` — Mic capture (SpeechRecognition) + TTS (Fish Audio with Samantha voice model)
- `samantha/brain.py` — Wraps `claude -p` subprocess, builds prompts with personality
- `samantha/personality.py` — The Samantha persona prompt
- `samantha/config.py` — Manages `~/.samantha/config.yaml`
- `samantha/ui.py` — Rich terminal display with colored status indicators

## Key Details
- Voice model: Fish Audio `474887f7949b4d1ab3e626cddf82613a` (OS1 Samantha / Scarlett Johansson from Her)
- Speech speed: 0.95x (configurable)
- Claude is called via `claude -p` with stdin, uses the user's Max subscription (zero API cost)
- Conversation history maintained in memory (last 10 exchanges)
- Phrase time limit: 30 seconds (configurable)
- All processing is local except: Google STT (free), Fish Audio TTS (paid, ~$1.25/hr of speech)

## Commands
- `samantha` — Full voice mode (speak + hear)
- `samantha --text` — Text only (type + hear)
- `samantha --no-voice` — Voice input, text output (speak + read)
- `samantha config` — Set Fish Audio API key
