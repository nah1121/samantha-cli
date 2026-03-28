"""Local text-to-speech using Piper (offline, 100% free).

Uses Piper TTS for high-quality, fast voice synthesis. Works offline with no API costs.
Fully private - no data sent to cloud services.
"""

from __future__ import annotations

import os
import platform
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


class LocalTTS:
    """Local text-to-speech using Piper.

    Args:
        voice: Voice model name (default: en_US-lessac-medium for high quality female voice)
        speed: Speech speed multiplier (default: 1.0, range: 0.5-2.0)
        model_dir: Directory to store downloaded voice models (default: ~/.samantha/voices)
    """

    # Available voice models - mapping friendly names to actual model names
    VOICES = {
        "samantha": "en_US-lessac-medium",  # High quality female (similar to Her)
        "amy": "en_US-amy-medium",  # Female
        "kathleen": "en_US-kathleen-low",  # Older female
        "libritts": "en_US-libritts-high",  # Multi-speaker high quality
        "ryan": "en_US-ryan-high",  # Male
    }

    def __init__(
        self,
        voice: str = "samantha",
        speed: float = 1.0,
        model_dir: Optional[Path] = None,
    ):
        # Resolve voice name to actual model
        if voice in self.VOICES:
            self.voice_model = self.VOICES[voice]
        else:
            self.voice_model = voice  # Allow direct model names too

        self.speed = max(0.5, min(2.0, speed))  # Clamp to valid range

        # Set up model directory
        if model_dir is None:
            model_dir = Path.home() / ".samantha" / "voices"
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self._temp_dir = Path(tempfile.mkdtemp(prefix="samantha_tts_"))

    def _get_model_path(self) -> Path:
        """Get path to voice model, downloading if necessary."""
        model_path = self.model_dir / f"{self.voice_model}.onnx"
        config_path = self.model_dir / f"{self.voice_model}.onnx.json"

        # Check if model already exists
        if model_path.exists() and config_path.exists():
            return model_path

        # Download model using piper
        print(f"Downloading voice model: {self.voice_model}...")
        try:
            # Try to download using piper's built-in download
            from piper.download import ensure_voice_exists, get_voices

            ensure_voice_exists(
                self.voice_model,
                [self.model_dir],
                self.model_dir,
            )
        except Exception as e:
            # Fallback: manual download
            print(f"Using fallback download method: {e}")
            self._download_model_manual(model_path, config_path)

        return model_path

    def _download_model_manual(self, model_path: Path, config_path: Path):
        """Manually download model from Piper repository."""
        import urllib.request

        base_url = f"https://github.com/rhasspy/piper/releases/download/v1.2.0/{self.voice_model}.onnx"

        try:
            # Download .onnx file
            print(f"Downloading {model_path.name}...")
            urllib.request.urlretrieve(f"{base_url}", str(model_path))

            # Download .onnx.json config file
            print(f"Downloading {config_path.name}...")
            urllib.request.urlretrieve(f"{base_url}.json", str(config_path))

            print("Download complete!")
        except Exception as e:
            raise RuntimeError(
                f"Failed to download voice model {self.voice_model}. "
                f"Error: {e}. Please download manually from: {base_url}"
            ) from e

    def generate_audio(self, text: str, output_path: Optional[str] = None) -> str:
        """Generate audio from text and save to file.

        Args:
            text: Text to convert to speech
            output_path: Where to save the audio file (default: temp file)

        Returns:
            Path to the generated audio file (WAV format)
        """
        if not text.strip():
            raise ValueError("Cannot generate audio from empty text")

        # Get or create output path
        if output_path is None:
            output_path = str(self._temp_dir / "output.wav")

        # Get model path (downloads if needed)
        model_path = self._get_model_path()

        try:
            # Use piper-tts library
            from piper import PiperVoice

            voice = PiperVoice.load(str(model_path))

            # Generate audio
            with open(output_path, "wb") as f:
                # Synthesize with length scale (inverse of speed)
                length_scale = 1.0 / self.speed
                voice.synthesize(text, f, length_scale=length_scale)

            return output_path

        except ImportError:
            # Fallback: use piper CLI if library import fails
            return self._generate_with_cli(text, output_path, model_path)

    def _generate_with_cli(self, text: str, output_path: str, model_path: Path) -> str:
        """Generate audio using piper CLI (fallback)."""
        try:
            # Find piper executable
            piper_cmd = "piper"
            if platform.system() == "Windows":
                piper_cmd = "piper.exe"

            # Run piper CLI
            cmd = [
                piper_cmd,
                "--model", str(model_path),
                "--output_file", output_path,
                "--length_scale", str(1.0 / self.speed),
            ]

            result = subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                capture_output=True,
                check=True,
            )

            return output_path

        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            raise RuntimeError(
                f"Piper TTS failed. Make sure piper is installed: pip install piper-tts\n"
                f"Error: {e}"
            ) from e

    def speak(self, text: str) -> str:
        """Generate audio and return path (for compatibility with voice.py)."""
        return self.generate_audio(text)

    def play_audio(self, path: str) -> None:
        """Play an audio file using the system audio player."""
        import subprocess
        import platform

        system = platform.system()

        try:
            if system == "Darwin":
                # macOS: afplay
                subprocess.run(["afplay", path], check=True, capture_output=True)
            elif system == "Windows":
                # Windows: use built-in player or ffplay
                try:
                    # Try PowerShell's built-in audio playback
                    ps_cmd = f'(New-Object Media.SoundPlayer "{path}").PlaySync()'
                    subprocess.run(
                        ["powershell", "-Command", ps_cmd],
                        check=True,
                        capture_output=True,
                    )
                except subprocess.CalledProcessError:
                    # Fallback to ffplay
                    subprocess.run(
                        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path],
                        check=True,
                        capture_output=True,
                    )
            else:
                # Linux: try multiple players
                for player_cmd in [
                    ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path],
                    ["aplay", path],
                    ["paplay", path],
                    ["mpv", "--no-video", "--really-quiet", path],
                ]:
                    try:
                        subprocess.run(player_cmd, check=True, capture_output=True)
                        return
                    except (FileNotFoundError, subprocess.CalledProcessError):
                        continue

                raise RuntimeError(
                    "No audio player found. Install: sudo apt install ffmpeg"
                )

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to play audio: {e}") from e

    def cleanup(self):
        """Clean up temporary files."""
        try:
            for f in self._temp_dir.glob("*"):
                try:
                    f.unlink()
                except OSError:
                    pass
            self._temp_dir.rmdir()
        except OSError:
            pass
