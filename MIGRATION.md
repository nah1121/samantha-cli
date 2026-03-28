# Migration Guide: Cloud to Local Mode

If you're an existing Samantha user with the cloud version (Fish Audio), here's how to switch to the new 100% local and free mode.

## What's Changed

**Before (Cloud):**
- STT: Google Speech Recognition (free, online)
- TTS: Fish Audio (paid, ~$1.25/hr)
- Required: Fish Audio API key
- Cost: ~$1.25 per hour of speech

**After (Local):**
- STT: OpenAI Whisper (free, offline)
- TTS: Piper (free, offline)
- Required: Nothing! (just install packages)
- Cost: $0

## Migration Steps

### 1. Update your installation

```bash
cd samantha-cli
git pull origin main
pip install -e .
```

### 2. Install new dependencies

```bash
# Quick way - run the setup script
samantha setup

# OR manually install
pip install faster-whisper piper-tts numpy
```

### 3. Update your config (automatic)

The new version automatically defaults to local mode. Your existing config will be preserved, but local engines will be preferred.

Check your config:
```bash
samantha config
```

You should see:
```yaml
stt_engine: local    # New!
tts_engine: local    # New!
whisper_model: base  # New!
piper_voice: samantha  # New!
```

### 4. Optional: Keep using cloud mode

If you prefer the cloud version, just set the engines back:

```bash
samantha config stt_engine cloud
samantha config tts_engine cloud
```

Your Fish Audio API key is still stored and will work.

### 5. Test it

```bash
# Text mode first (no mic needed)
samantha --text
# Type: "Hello"
# You should hear Samantha's voice (now from Piper, not Fish Audio)

# Full voice mode
samantha
# Speak into your mic - Whisper will transcribe locally
```

## Configuration Options

### Switch engines individually

You can mix and match:

```bash
# Use local STT, cloud TTS
samantha config stt_engine local
samantha config tts_engine cloud

# Use cloud STT, local TTS
samantha config stt_engine cloud
samantha config tts_engine local

# Use all local (default)
samantha config stt_engine local
samantha config tts_engine local
```

### Adjust Whisper model

```bash
# Faster (for slower CPUs)
samantha config whisper_model tiny

# Better accuracy (for powerful CPUs/GPUs)
samantha config whisper_model small
samantha config whisper_model medium  # Needs GPU

# Enable GPU
samantha config whisper_device cuda
```

### Change voice

```bash
# Try different Piper voices
samantha config piper_voice amy
samantha config piper_voice kathleen
samantha config piper_voice ryan
```

## Troubleshooting

### "Local STT (Whisper) not available"

Install dependencies:
```bash
pip install faster-whisper pyaudio numpy
```

### "Local TTS (Piper) not available"

Install Piper:
```bash
pip install piper-tts
```

### Models taking long to download

First run downloads ~200MB of models:
- Whisper base model: ~140MB
- Piper voice model: ~60MB

This is one-time. After that, everything runs offline.

### Performance issues

Try a smaller Whisper model:
```bash
samantha config whisper_model tiny  # Fastest
```

Or enable GPU if available:
```bash
samantha config whisper_device cuda
```

## Comparison

| Feature | Cloud (Old) | Local (New) | Winner |
|---|---|---|---|
| **Cost** | ~$1.25/hr | $0 | ✅ Local |
| **Privacy** | Data sent to cloud | 100% on-device | ✅ Local |
| **Internet** | Required | Optional | ✅ Local |
| **Setup time** | Instant (with API key) | ~1 min (model download) | Cloud |
| **Quality** | Excellent | Excellent | Tie |
| **Latency** | Fast (network dependent) | Fast (CPU/GPU dependent) | Tie |
| **Customization** | Limited | High (multiple models/voices) | ✅ Local |

## Recommendation

**Switch to local mode!** Unless you have a specific reason to use cloud services:
- ✅ Save money (no more Fish Audio costs)
- ✅ Better privacy (no data sent to cloud)
- ✅ Works offline
- ✅ Same quality
- ✅ More customization

The cloud mode is still available as a fallback option if needed.

## Questions?

See the main [README.md](README.md) for full documentation, or run:

```bash
samantha config  # View your settings
samantha --help  # See all commands
```
