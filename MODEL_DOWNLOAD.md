# Model Auto-Download Behavior

This document explains how Samantha CLI automatically downloads Whisper and Piper models without returning errors.

## Overview

Both Whisper (STT) and Piper (TTS) models are downloaded automatically on first use. The implementation ensures:
- ✅ No manual downloads required
- ✅ Clear progress messages during download
- ✅ Helpful error messages if downloads fail
- ✅ Graceful fallback mechanisms
- ✅ One-time download (cached for future use)

## Whisper Model Download (STT)

**Location:** `samantha/stt_local.py` - `model` property (lines 64-110)

### How It Works

1. **Lazy Loading:** Model is only loaded when first accessed (when you first speak)
2. **Cache Check:** Checks if model already exists in `~/.cache/huggingface/hub/`
3. **Download Progress:** If not cached, shows progress message:
   ```
   Downloading Whisper base model (~145MB)...
   This is a one-time download. Future use will be instant.
   ```
4. **Automatic Download:** `faster-whisper` library downloads from Hugging Face automatically
5. **Success Message:** Shows "✓ Whisper model ready!" when complete

### Error Handling

If download fails, provides clear error message:
```
Failed to load Whisper model 'base'.
This might be due to:
  1. No internet connection (models download on first use)
  2. Insufficient disk space (~145MB needed)
  3. Missing dependencies: pip install faster-whisper
Error details: [specific error]
```

### Model Sizes

- `tiny`: ~75 MB
- `base`: ~145 MB (default)
- `small`: ~488 MB
- `medium`: ~1.5 GB
- `large-v3`: ~3 GB

## Piper Voice Model Download (TTS)

**Location:** `samantha/tts_local.py` - `_get_model_path()` method (lines 57-105)

### How It Works

1. **Check Existence:** Checks if model exists in `~/.samantha/voices/`
2. **Download Progress:** If not present, shows:
   ```
   Downloading Piper voice model 'en_US-lessac-medium' (~60MB)...
   This is a one-time download. Future use will be instant.
   ```
3. **Primary Method:** Uses piper's `ensure_voice_exists()` function
4. **Fallback Method:** If primary fails, uses direct urllib download from GitHub
5. **Success Message:** Shows "✓ Voice model ready!" when complete

### Error Handling (lines 107-144)

Multiple layers of error handling:

1. **Import Error:** If piper.download not available, uses manual download
2. **Primary Failure:** Falls back to manual download
3. **404 Error:** Shows available voice names:
   ```
   Voice model 'invalid-name' not found.
   Available voices: samantha, amy, kathleen, ryan, libritts
   Change voice with: samantha config piper_voice <voice_name>
   ```
4. **Network Error:** Clear message about internet connection
5. **Other Errors:** Shows download URL for manual download

### Manual Download Fallback

Downloads directly from GitHub:
```
https://github.com/rhasspy/piper/releases/download/v1.2.0/{model_name}.onnx
https://github.com/rhasspy/piper/releases/download/v1.2.0/{model_name}.onnx.json
```

## Voice Engine Integration

**Location:** `samantha/voice.py` - `_listen_local()` and `_generate_audio_local()` methods

### STT Integration (lines 182-201)

- Preserves `RuntimeError` from Whisper (includes download errors)
- Adds troubleshooting tips for other errors
- Suggests switching to cloud mode as alternative

### TTS Integration (lines 249-264)

- Preserves `RuntimeError` from Piper (includes download errors)
- Adds troubleshooting tips for other errors
- Suggests switching to cloud mode as alternative

## First-Time User Experience

### Successful Download Flow

```
User: samantha
System: Downloading Whisper base model (~145MB)...
        This is a one-time download. Future use will be instant.

        [downloads in background]

        ✓ Whisper model ready!

Samantha: ● Listening...
[User speaks]

Samantha: ● Thinking...
[Claude processes]

System: Downloading Piper voice model 'en_US-lessac-medium' (~60MB)...
        This is a one-time download. Future use will be instant.

        [downloads in background]

        ✓ Voice model ready!

Samantha: [Speaks response]
```

### Subsequent Uses

```
User: samantha
Samantha: ● Listening...
[No downloads - instant startup]
```

## Error Recovery

### No Internet Connection

**Error Message:**
```
Failed to load Whisper model 'base'.
This might be due to:
  1. No internet connection (models download on first use)
  2. Insufficient disk space (~145MB needed)
  3. Missing dependencies: pip install faster-whisper
```

**User Action:**
- Connect to internet
- Retry: `samantha`
- Or use cloud mode: `samantha config stt_engine cloud`

### Invalid Voice Name

**Error Message:**
```
Voice model 'invalid-name' not found.
Available voices: samantha, amy, kathleen, ryan, libritts
Change voice with: samantha config piper_voice <voice_name>
```

**User Action:**
```bash
samantha config piper_voice samantha  # Fix voice name
samantha  # Try again
```

### Disk Space Issues

Models require:
- Whisper: 75MB - 3GB (depending on model)
- Piper: ~60MB per voice
- Total: ~200MB minimum for default setup

## Testing

All modules tested and verified:
- ✅ Syntax validation passes
- ✅ Import tests pass
- ✅ VoiceEngine initialization works
- ✅ Error messages are clear
- ✅ Fallback mechanisms work

## Summary

The automatic download system ensures that users never need to manually download models. The implementation:

1. **Downloads automatically** when first needed
2. **Shows clear progress** during downloads
3. **Provides helpful errors** if something goes wrong
4. **Has fallback mechanisms** for reliability
5. **Caches for future use** (one-time download)

Users simply run `samantha` and everything works - no manual downloads, no errors, just seamless setup.
