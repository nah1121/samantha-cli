"""Local speech-to-text using Whisper (offline, 100% free).

Uses faster-whisper for optimized performance. Works on CPU with optional GPU acceleration.
Fully offline and private - no data sent to cloud services.
"""

from __future__ import annotations

import io
import wave
import tempfile
from pathlib import Path
from typing import Optional

import numpy as np
import pyaudio


class LocalSTT:
    """Local speech-to-text using faster-whisper.

    Args:
        model_size: Whisper model size - tiny, base, small, medium, large-v3 (default: base)
        device: Device to run on - "cpu", "cuda", or "auto" for auto-detection (default: auto)
        compute_type: Precision - "int8", "float16", "float32" (default: int8 for CPU, float16 for GPU)
        language: Language code for transcription (default: en for English)
        sample_rate: Audio sample rate in Hz (default: 16000)
    """

    def __init__(
        self,
        model_size: str = "base",
        device: str = "auto",
        compute_type: Optional[str] = None,
        language: str = "en",
        sample_rate: int = 16000,
    ):
        self.model_size = model_size
        self.language = language
        self.sample_rate = sample_rate

        # Auto-detect device and compute type
        if device == "auto":
            device = self._detect_device()
        self.device = device

        if compute_type is None:
            compute_type = "float16" if device == "cuda" else "int8"
        self.compute_type = compute_type

        self._model = None
        self._pyaudio = None

    def _detect_device(self) -> str:
        """Auto-detect if CUDA is available."""
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
        except ImportError:
            pass
        return "cpu"

    @property
    def model(self):
        """Lazily initialize the Whisper model."""
        if self._model is None:
            from faster_whisper import WhisperModel

            # Download and cache model on first use
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
        return self._model

    def transcribe_file(self, audio_path: str) -> str:
        """Transcribe audio from a file path.

        Args:
            audio_path: Path to audio file (WAV, MP3, etc.)

        Returns:
            Transcribed text
        """
        segments, info = self.model.transcribe(
            audio_path,
            language=self.language,
            beam_size=5,
            vad_filter=True,  # Voice activity detection to remove silence
            vad_parameters=dict(
                min_silence_duration_ms=500,  # Ignore silence shorter than this
            ),
        )

        # Combine all segments into single text
        text = " ".join(segment.text.strip() for segment in segments)
        return text.strip()

    def transcribe_audio_data(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        """Transcribe audio from raw audio bytes.

        Args:
            audio_data: Raw audio data (PCM format)
            sample_rate: Sample rate of audio data

        Returns:
            Transcribed text
        """
        # Save to temporary file (faster-whisper requires file input)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            # Write WAV header
            with wave.open(tmp.name, "wb") as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data)

            tmp_path = tmp.name

        try:
            return self.transcribe_file(tmp_path)
        finally:
            # Clean up temp file
            try:
                Path(tmp_path).unlink()
            except OSError:
                pass

    def listen(
        self,
        timeout: int = 10,
        phrase_time_limit: int = 60,
        energy_threshold: int = 300,
        pause_threshold: float = 1.0,
    ) -> Optional[str]:
        """Listen to microphone and return transcribed text.

        Args:
            timeout: Maximum seconds to wait for speech to start
            phrase_time_limit: Maximum seconds for a single phrase
            energy_threshold: Minimum audio energy to consider as speech
            pause_threshold: Seconds of silence before stopping

        Returns:
            Transcribed text, or None if nothing detected
        """
        if self._pyaudio is None:
            self._pyaudio = pyaudio.PyAudio()

        try:
            # Open microphone stream
            stream = self._pyaudio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=1024,
            )

            frames = []
            silent_chunks = 0
            started = False
            chunks_per_second = self.sample_rate // 1024

            # Calculate thresholds in chunks
            timeout_chunks = timeout * chunks_per_second
            pause_chunks = int(pause_threshold * chunks_per_second)
            max_chunks = phrase_time_limit * chunks_per_second

            chunk_count = 0

            while chunk_count < timeout_chunks + max_chunks:
                data = stream.read(1024, exception_on_overflow=False)
                chunk_count += 1

                # Convert to numpy array to calculate energy
                audio_data = np.frombuffer(data, dtype=np.int16)
                energy = np.abs(audio_data).mean()

                if energy > energy_threshold:
                    # Speech detected
                    if not started:
                        started = True
                        chunk_count = 0  # Reset counter after speech starts
                    frames.append(data)
                    silent_chunks = 0
                else:
                    # Silence
                    if started:
                        frames.append(data)
                        silent_chunks += 1

                        # Stop if we've been silent for pause_threshold
                        if silent_chunks > pause_chunks:
                            break
                    elif chunk_count >= timeout_chunks:
                        # Timeout waiting for speech
                        stream.stop_stream()
                        stream.close()
                        return None

                # Stop if we've recorded too long
                if started and len(frames) > max_chunks:
                    break

            stream.stop_stream()
            stream.close()

            if not frames:
                return None

            # Combine all audio frames
            audio_data = b"".join(frames)

            # Transcribe
            return self.transcribe_audio_data(audio_data, self.sample_rate)

        except Exception as e:
            if stream and stream.is_active():
                stream.stop_stream()
                stream.close()
            raise RuntimeError(f"Error during audio capture: {e}") from e

    def cleanup(self):
        """Release audio resources."""
        if self._pyaudio is not None:
            self._pyaudio.terminate()
            self._pyaudio = None
