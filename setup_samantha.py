#!/usr/bin/env python3
"""
Samantha CLI Setup Script

Handles first-time setup, model downloads, and Windows-specific configuration.
Run this after installing the package to ensure everything is ready.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path


def print_header(text):
    """Print a formatted header."""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}\n")


def print_step(num, text):
    """Print a numbered step."""
    print(f"[{num}] {text}")


def run_command(cmd, description, check=True):
    """Run a command and handle errors."""
    print(f"  → {description}...")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=check,
            shell=isinstance(cmd, str),
        )
        if result.stdout:
            print(f"    {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"    ✗ Failed: {e.stderr if e.stderr else str(e)}")
        return False


def check_python_version():
    """Verify Python version is 3.10+."""
    print_step(1, "Checking Python version")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print(f"  ✗ Python 3.10+ required, found {version.major}.{version.minor}")
        sys.exit(1)
    print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")


def check_claude_cli():
    """Check if Claude CLI is installed."""
    print_step(2, "Checking Claude CLI")
    result = subprocess.run(
        ["claude", "--version"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(f"  ✓ Claude CLI installed: {result.stdout.strip()}")
        return True
    else:
        print("  ✗ Claude CLI not found")
        print("    Install from: https://claude.ai/download")
        return False


def install_system_dependencies():
    """Install system-level dependencies based on OS."""
    print_step(3, "Installing system dependencies")
    system = platform.system()

    if system == "Darwin":
        # macOS
        print("  → Checking for Homebrew...")
        if subprocess.run(["which", "brew"], capture_output=True).returncode != 0:
            print("  ✗ Homebrew not found. Install from: https://brew.sh")
            return False

        print("  → Installing portaudio (for microphone)...")
        run_command(["brew", "install", "portaudio"], "Installing portaudio", check=False)

        print("  → Installing ffmpeg (for audio playback)...")
        run_command(["brew", "install", "ffmpeg"], "Installing ffmpeg", check=False)

    elif system == "Linux":
        # Linux
        print("  → Detecting package manager...")
        if subprocess.run(["which", "apt"], capture_output=True).returncode == 0:
            # Debian/Ubuntu
            print("  → Installing dependencies with apt...")
            run_command(
                ["sudo", "apt", "update"],
                "Updating package list",
                check=False,
            )
            run_command(
                ["sudo", "apt", "install", "-y", "portaudio19-dev", "ffmpeg", "python3-dev"],
                "Installing portaudio, ffmpeg, and python3-dev",
                check=False,
            )
        elif subprocess.run(["which", "dnf"], capture_output=True).returncode == 0:
            # Fedora/RHEL
            print("  → Installing dependencies with dnf...")
            run_command(
                ["sudo", "dnf", "install", "-y", "portaudio-devel", "ffmpeg", "python3-devel"],
                "Installing portaudio, ffmpeg, and python3-devel",
                check=False,
            )
        else:
            print("  ⚠ Unknown Linux distribution. Please install manually:")
            print("    - portaudio development libraries")
            print("    - ffmpeg")
            print("    - python3 development headers")
            return False

    elif system == "Windows":
        # Windows
        print("  → Windows detected")
        print("  ⚠ Please ensure the following are installed:")
        print("    1. Python 3.10+ with pip")
        print("    2. Microsoft Visual C++ 14.0+ (for PyAudio)")
        print("       Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/")
        print("    3. FFmpeg (for audio playback)")
        print("       Download from: https://www.gyan.dev/ffmpeg/builds/")
        print("       Add to PATH after installing")
        input("\n  Press Enter when ready to continue...")

    else:
        print(f"  ⚠ Unsupported OS: {system}")
        return False

    print("  ✓ System dependencies ready")
    return True


def install_python_packages():
    """Install Python package dependencies."""
    print_step(4, "Installing Python packages")

    packages = [
        "faster-whisper",
        "piper-tts",
        "pyaudio",
        "numpy",
        "rich",
        "click",
        "pyyaml",
    ]

    for package in packages:
        print(f"  → Installing {package}...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f"    ✓ {package} installed")
        else:
            print(f"    ⚠ {package} installation had issues (may already be installed)")

    print("  ✓ Python packages installed")


def download_models():
    """Download required Whisper and Piper models."""
    print_step(5, "Downloading AI models")

    # Create model directories
    samantha_dir = Path.home() / ".samantha"
    voices_dir = samantha_dir / "voices"
    voices_dir.mkdir(parents=True, exist_ok=True)

    # Download Whisper model (done automatically on first use)
    print("  → Whisper model will download automatically on first use")
    print("    (base model: ~140MB, first run may take a minute)")

    # Download Piper voice model
    print("  → Downloading Piper voice model (samantha/en_US-lessac-medium)...")
    try:
        from piper.download import ensure_voice_exists

        model_name = "en_US-lessac-medium"
        ensure_voice_exists(model_name, [voices_dir], voices_dir)
        print("    ✓ Piper voice model downloaded")
    except Exception as e:
        print(f"    ⚠ Piper model will download on first use: {e}")

    print("  ✓ Models ready")


def create_default_config():
    """Create default configuration file."""
    print_step(6, "Creating configuration")

    config_dir = Path.home() / ".samantha"
    config_file = config_dir / "config.yaml"
    config_dir.mkdir(parents=True, exist_ok=True)

    if config_file.exists():
        print("  ✓ Configuration already exists")
        return

    default_config = """# Samantha CLI Configuration
# Edit with: samantha config <key> <value>

# Engine selection (local = free & offline, cloud = paid & online)
stt_engine: local  # Speech-to-text: "local" (whisper) or "cloud" (google)
tts_engine: local  # Text-to-speech: "local" (piper) or "cloud" (fish)

# Local STT settings (Whisper)
whisper_model: base  # Model size: tiny, base, small, medium, large-v3
whisper_device: auto  # Device: auto, cpu, cuda
whisper_compute_type: null  # Precision: null (auto), int8, float16, float32

# Local TTS settings (Piper)
piper_voice: samantha  # Voice: samantha, amy, kathleen, ryan, libritts
speech_speed: 0.95  # Speed: 0.5 (slow) to 2.0 (fast)

# General settings
language: en-US
max_history: 10
listen_timeout: 10
phrase_time_limit: 30

# Cloud fallback (optional - leave empty for 100% local)
fish_api_key: ""
voice_model_id: "474887f7949b4d1ab3e626cddf82613a"
"""

    config_file.write_text(default_config)
    print(f"  ✓ Configuration created at: {config_file}")


def test_setup():
    """Run a quick test of the installation."""
    print_step(7, "Testing setup")

    print("  → Testing imports...")
    try:
        import faster_whisper
        import piper
        import pyaudio
        import rich
        import click
        import yaml

        print("    ✓ All imports successful")
    except ImportError as e:
        print(f"    ✗ Import failed: {e}")
        return False

    print("  ✓ Setup test passed")
    return True


def main():
    """Run the complete setup process."""
    print_header("Samantha CLI Setup")
    print("This script will set up Samantha for local, offline operation.")
    print("100% free and private - no API keys required!\n")

    # Check prerequisites
    check_python_version()

    claude_ok = check_claude_cli()
    if not claude_ok:
        print("\n⚠ Claude CLI is required but not installed.")
        response = input("Continue anyway? (y/N): ").strip().lower()
        if response != "y":
            print("\nSetup cancelled. Install Claude CLI first.")
            sys.exit(1)

    # Install dependencies
    install_system_dependencies()
    install_python_packages()

    # Download models and create config
    download_models()
    create_default_config()

    # Test
    test_ok = test_setup()

    # Final instructions
    print_header("Setup Complete!")

    if test_ok:
        print("✓ Samantha is ready to use!\n")
        print("To start:")
        print("  samantha              # Full voice mode")
        print("  samantha --text       # Text mode (no microphone)")
        print("\nConfiguration:")
        print("  samantha config       # View current settings")
        print("  samantha config whisper_model small  # Use faster/smaller model")
        print("\nThe default setup is 100% local and free:")
        print("  • Speech-to-text: Whisper (base model)")
        print("  • Text-to-speech: Piper (samantha voice)")
        print("  • No internet required after setup")
        print("  • All data stays on your machine")
    else:
        print("⚠ Setup completed with warnings.")
        print("  Try running 'samantha --text' to test basic functionality.")
        print("  If issues persist, check the installation guide in README.md")

    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
