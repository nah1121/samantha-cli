"""Voice engine -- speech recognition and text-to-speech.

Handles microphone input via SpeechRecognition (Google free STT)
and audio output via Fish Audio TTS with the Samantha voice model.
"""

from __future__ import annotations

import io
import os
import tempfile
from pathlib import Path

import pygame

from samantha import config as cfg


class VoiceEngine:
    """Manages speech-to-text and text-to-speech.

    Args:
        fish_api_key: Fish Audio API key for TTS.
        voice_model_id: Fish Audio voice model reference ID.
        speech_speed: TTS playback speed (0.5 - 2.0).
        language: Language code for speech recognition.
    """

    def __init__(
        self,
        fish_api_key: str = "",
        voice_model_id: str = "",
        speech_speed: float = 0.95,
        language: str = "en-US",
        listen_timeout: int = 10,
        phrase_time_limit: int = 30,
    ) -> None:
        self.fish_api_key = fish_api_key
        self.voice_model_id = voice_model_id or cfg.DEFAULTS["voice_model_id"]
        self.speech_speed = speech_speed
        self.language = language
        self.listen_timeout = listen_timeout
        self.phrase_time_limit = phrase_time_limit

        self._fish_client = None
        self._tts_config = None
        self._recognizer = None
        self._pygame_initialized = False
        self._temp_dir = Path(tempfile.mkdtemp(prefix="samantha_"))

    @property
    def tts_available(self) -> bool:
        """Check whether TTS is configured."""
        return bool(self.fish_api_key)

    @property
    def stt_available(self) -> bool:
        """Check whether speech recognition is available."""
        try:
            import speech_recognition as sr  # noqa: F401
            return True
        except ImportError:
            return False

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

    def _init_pygame(self) -> None:
        """Lazily initialize pygame mixer for audio playback."""
        if self._pygame_initialized:
            return

        # Suppress pygame welcome message
        os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
        self._pygame_initialized = True

    def _init_recognizer(self):
        """Lazily initialize the speech recognizer."""
        if self._recognizer is not None:
            return self._recognizer

        import speech_recognition as sr

        self._recognizer = sr.Recognizer()
        # Tweak energy threshold for better detection
        self._recognizer.dynamic_energy_threshold = True
        return self._recognizer

    def listen(self) -> str | None:
        """Listen for speech via the microphone and return transcribed text.

        Returns:
            Transcribed text, or None if nothing was understood.

        Raises:
            RuntimeError: If the microphone is not accessible.
        """
        import speech_recognition as sr

        recognizer = self._init_recognizer()

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
                "Check your internet connection."
            ) from e

    def speak(self, text: str) -> None:
        """Convert text to speech and play it through the speakers.

        Falls back to just displaying the text if TTS is not configured.

        Args:
            text: The text to speak.
        """
        if not self.tts_available:
            return  # Caller handles display; we just skip audio

        self._init_fish()
        self._init_pygame()

        try:
            audio = self._fish_client.tts.convert(
                text=text,
                config=self._tts_config,
            )

            # Write audio to a temp file for pygame playback
            audio_path = self._temp_dir / "response.mp3"

            # fish-audio-sdk returns an iterable of bytes chunks
            with open(audio_path, "wb") as f:
                for chunk in audio:
                    f.write(chunk)

            pygame.mixer.music.load(str(audio_path))
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                pygame.time.wait(50)

        except Exception as e:
            # TTS failure should not crash the app -- degrade gracefully
            raise TTSError(f"Text-to-speech failed: {e}") from e

    def stop_speaking(self) -> None:
        """Stop any currently playing audio."""
        if self._pygame_initialized and pygame.mixer.get_init():
            pygame.mixer.music.stop()

    def cleanup(self) -> None:
        """Release audio resources."""
        if self._pygame_initialized:
            pygame.mixer.quit()
            self._pygame_initialized = False

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
