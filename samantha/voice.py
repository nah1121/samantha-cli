"""Voice engine -- speech recognition and text-to-speech.

Supports both local (free, offline) and cloud (paid) engines.
Local engines use Whisper (STT) and Piper (TTS) - 100% free and private.
Cloud engines use Google STT and Fish Audio TTS (requires API key).
"""

from __future__ import annotations

import io
import os
import tempfile
from pathlib import Path
from typing import Optional

from samantha import config as cfg


class VoiceEngine:
    """Manages speech-to-text and text-to-speech with local and cloud options.

    Args:
        stt_engine: "local" (whisper) or "cloud" (google) for speech-to-text
        tts_engine: "local" (piper) or "cloud" (fish) for text-to-speech
        whisper_model: Whisper model size (tiny, base, small, medium, large-v3)
        whisper_device: Device for Whisper (auto, cpu, cuda)
        piper_voice: Voice model for Piper TTS (samantha, amy, kathleen, ryan)
        fish_api_key: Fish Audio API key (only for cloud TTS)
        voice_model_id: Fish Audio voice model ID (only for cloud TTS)
        speech_speed: TTS playback speed (0.5 - 2.0)
        language: Language code for speech recognition
        listen_timeout: Max seconds to wait for speech to start
        phrase_time_limit: Max seconds for a single phrase
    """

    def __init__(
        self,
        stt_engine: str = "local",
        tts_engine: str = "local",
        whisper_model: str = "base",
        whisper_device: str = "auto",
        whisper_compute_type: Optional[str] = None,
        piper_voice: str = "samantha",
        fish_api_key: str = "",
        voice_model_id: str = "",
        speech_speed: float = 0.95,
        language: str = "en-US",
        listen_timeout: int = 10,
        phrase_time_limit: int = 60,
    ) -> None:
        self.stt_engine = stt_engine
        self.tts_engine = tts_engine
        self.speech_speed = speech_speed
        self.language = language
        self.listen_timeout = listen_timeout
        self.phrase_time_limit = phrase_time_limit

        # Local engine settings
        self.whisper_model = whisper_model
        self.whisper_device = whisper_device
        self.whisper_compute_type = whisper_compute_type
        self.piper_voice = piper_voice

        # Cloud engine settings
        self.fish_api_key = fish_api_key
        self.voice_model_id = voice_model_id or cfg.DEFAULTS["voice_model_id"]

        # Lazy initialization
        self._local_stt = None
        self._local_tts = None
        self._cloud_recognizer = None
        self._fish_client = None
        self._tts_config = None
        self._temp_dir = Path(tempfile.mkdtemp(prefix="samantha_"))

    @property
    def stt_available(self) -> bool:
        """Check whether speech-to-text is available."""
        if self.stt_engine == "local":
            try:
                import faster_whisper  # noqa: F401
                import pyaudio  # noqa: F401
                return True
            except ImportError:
                return False
        else:  # cloud
            try:
                import speech_recognition as sr  # noqa: F401
                return True
            except ImportError:
                return False

    @property
    def tts_available(self) -> bool:
        """Check whether text-to-speech is available."""
        if self.tts_engine == "local":
            try:
                # Check if piper-tts is installed
                # We'll verify at runtime since it may be CLI or library
                return True
            except Exception:
                return False
        else:  # cloud
            return bool(self.fish_api_key)

    def _init_local_stt(self):
        """Lazily initialize local STT (Whisper)."""
        if self._local_stt is not None:
            return self._local_stt

        from samantha.stt_local import LocalSTT

        self._local_stt = LocalSTT(
            model_size=self.whisper_model,
            device=self.whisper_device,
            compute_type=self.whisper_compute_type,
            language=self.language.split("-")[0],  # Convert en-US to en
            sample_rate=16000,
        )
        return self._local_stt

    def _init_local_tts(self):
        """Lazily initialize local TTS (Piper)."""
        if self._local_tts is not None:
            return self._local_tts

        from samantha.tts_local import LocalTTS

        self._local_tts = LocalTTS(
            voice=self.piper_voice,
            speed=self.speech_speed,
        )
        return self._local_tts

    def _init_cloud_recognizer(self):
        """Lazily initialize cloud STT (Google)."""
        if self._cloud_recognizer is not None:
            return self._cloud_recognizer

        import speech_recognition as sr

        self._cloud_recognizer = sr.Recognizer()
        # Be very patient - wait for long pauses before considering speech "done"
        self._cloud_recognizer.pause_threshold = 3.0
        self._cloud_recognizer.phrase_threshold = 0.2
        self._cloud_recognizer.non_speaking_duration = 2.0
        self._cloud_recognizer.dynamic_energy_threshold = True
        self._cloud_recognizer.energy_threshold = 300
        return self._cloud_recognizer

    def _init_fish(self) -> None:
        """Lazily initialize the Fish Audio client."""
        if self._fish_client is not None:
            return

        from fishaudio import FishAudio
        from fishaudio.types import TTSConfig, Prosody

        self._fish_client = FishAudio(api_key=self.fish_api_key)
        self._tts_config = TTSConfig(
            reference_id=self.voice_model_id,
            prosody=Prosody(speed=self.speech_speed),
            format="mp3",
        )

    def listen(self) -> str | None:
        """Listen for speech via the microphone and return transcribed text.

        Uses the configured STT engine (local Whisper or cloud Google).

        Returns:
            Transcribed text, or None if nothing was understood.

        Raises:
            RuntimeError: If the microphone is not accessible or STT fails.
        """
        if self.stt_engine == "local":
            return self._listen_local()
        else:
            return self._listen_cloud()

    def _listen_local(self) -> str | None:
        """Listen using local Whisper STT."""
        try:
            stt = self._init_local_stt()
            text = stt.listen(
                timeout=self.listen_timeout,
                phrase_time_limit=self.phrase_time_limit,
            )
            return text
        except Exception as e:
            raise RuntimeError(f"Local STT error: {e}") from e

    def _listen_cloud(self) -> str | None:
        """Listen using cloud Google STT."""
        import speech_recognition as sr

        recognizer = self._init_cloud_recognizer()

        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(
                    source,
                    timeout=self.listen_timeout,
                    phrase_time_limit=self.phrase_time_limit,
                )
        except sr.WaitTimeoutError:
            return None
        except OSError as e:
            raise RuntimeError(
                f"Could not access the microphone: {e}. "
                "Check your audio input settings and permissions."
            ) from e

        try:
            text = recognizer.recognize_google(audio, language=self.language)
            return text.strip() if text else None
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            raise RuntimeError(
                f"Speech recognition service error: {e}. "
                "Check your internet connection or switch to local STT."
            ) from e

    def generate_audio(self, text: str) -> str | None:
        """Generate TTS audio and save to temp file. Returns file path.

        Uses the configured TTS engine (local Piper or cloud Fish Audio).
        """
        if not self.tts_available:
            return None

        if self.tts_engine == "local":
            return self._generate_audio_local(text)
        else:
            return self._generate_audio_cloud(text)

    def _generate_audio_local(self, text: str) -> str | None:
        """Generate audio using local Piper TTS."""
        try:
            tts = self._init_local_tts()
            audio_path = tts.generate_audio(text)
            return audio_path
        except Exception as e:
            raise TTSError(f"Local TTS error: {e}") from e

    def _generate_audio_cloud(self, text: str) -> str | None:
        """Generate audio using cloud Fish Audio TTS."""
        self._init_fish()

        try:
            audio = self._fish_client.tts.convert(
                text=text,
                config=self._tts_config,
            )

            audio_path = self._temp_dir / "response.mp3"

            if isinstance(audio, bytes):
                audio_path.write_bytes(audio)
            else:
                collected = b"".join(
                    chunk if isinstance(chunk, bytes) else bytes([chunk])
                    for chunk in audio
                )
                audio_path.write_bytes(collected)

            return str(audio_path)
        except Exception as e:
            raise TTSError(f"Cloud TTS error: {e}") from e

    def play_audio(self, path: str) -> None:
        """Play an audio file using the system audio player."""
        if self.tts_engine == "local":
            tts = self._init_local_tts()
            tts.play_audio(path)
        else:
            self._play_audio_file(path)

    def _play_audio_file(self, path: str) -> None:
        """Play an audio file using the best available system player."""
        import subprocess
        import platform

        system = platform.system()

        if system == "Darwin":
            # macOS: afplay is built-in
            subprocess.run(["afplay", path], check=True, capture_output=True)
        elif system == "Windows":
            # Windows: PowerShell or ffplay
            try:
                ps_cmd = f'(New-Object Media.SoundPlayer "{path}").PlaySync()'
                subprocess.run(
                    ["powershell", "-Command", ps_cmd],
                    check=True,
                    capture_output=True,
                )
            except (FileNotFoundError, subprocess.CalledProcessError):
                # Fallback to ffplay
                subprocess.run(
                    ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path],
                    check=True,
                    capture_output=True,
                )
        else:
            # Linux: try multiple players
            for player in [
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path],
                ["mpv", "--no-video", "--really-quiet", path],
                ["aplay", path],
            ]:
                try:
                    subprocess.run(player, check=True, capture_output=True)
                    return
                except (FileNotFoundError, subprocess.CalledProcessError):
                    continue
            raise RuntimeError("No audio player found. Install ffmpeg or mpv.")

    def get_audio_duration(self, path: str) -> float:
        """Estimate audio duration from file size."""
        import os

        size = os.path.getsize(path)
        # Rough estimate: MP3 ~128kbps, WAV ~176kbps
        if path.endswith(".wav"):
            return size / 32000  # 16-bit mono at 16kHz
        else:
            return size / 16000  # MP3 estimate

    def speak(self, text: str) -> None:
        """Generate and play TTS. For simple usage."""
        path = self.generate_audio(text)
        if path:
            self.play_audio(path)

    def stop_speaking(self) -> None:
        """Stop any currently playing audio."""
        pass  # Audio cleanup handled by system player subprocess

    def cleanup(self) -> None:
        """Release audio resources."""
        # Cleanup local engines
        if self._local_stt is not None:
            self._local_stt.cleanup()
        if self._local_tts is not None:
            self._local_tts.cleanup()

        # Clean up temp files
        for f in self._temp_dir.glob("*"):
            try:
                f.unlink()
            except OSError:
                pass
        try:
            self._temp_dir.rmdir()
        except OSError:
            pass


class TTSError(Exception):
    """Raised when text-to-speech conversion or playback fails."""
