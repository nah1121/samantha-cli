"""CLI entry point for Samantha.

Provides the main `samantha` command and the `samantha config` subcommand.
"""

from __future__ import annotations

import sys

import click
from rich.console import Console

from samantha import __version__
from samantha import config as cfg
from samantha.brain import Brain
from samantha.ui import UI, Status
from samantha.voice import VoiceEngine, TTSError


@click.group(invoke_without_command=True)
@click.option("--text", "-t", is_flag=True, help="Text-only mode (no microphone).")
@click.option("--no-voice", "-n", is_flag=True, help="Disable TTS output.")
@click.version_option(version=__version__, prog_name="samantha")
@click.pass_context
def main(ctx: click.Context, text: bool, no_voice: bool) -> None:
    """Samantha -- Give Claude a voice. Inspired by Her."""
    if ctx.invoked_subcommand is not None:
        return

    _run_assistant(text_mode=text, no_voice=no_voice)


@main.command()
@click.argument("session_id", required=False)
def resume(session_id: str | None) -> None:
    """Resume a past conversation. Uses Claude's session history.

    Without arguments: continues the most recent Claude session.
    With a session ID: resumes that specific Claude session.
    """
    console = Console()
    settings = cfg.load()
    brain = Brain(max_history=settings["max_history"])

    if session_id:
        # Resume specific Claude session
        brain._resume_id = session_id
        console.print(f"  Resuming session {session_id}...", style="green")
    else:
        # Continue most recent Claude session
        brain._continue_mode = True
        console.print("  Continuing last session...", style="green")

    console.print()
    _run_assistant(text_mode=False, no_voice=False, brain=brain)


@main.command("config")
@click.argument("key", required=False)
@click.argument("value", required=False)
def config(key: str | None, value: str | None) -> None:
    """View or set configuration values.

    \b
    Examples:
        samantha config                  # Show all config
        samantha config fish_api_key     # Show one value
        samantha config fish_api_key sk-xxx  # Set a value
    """
    console = Console()

    if key is None:
        # Show all config
        current = cfg.load()
        console.print("\n  [bold magenta]Samantha Configuration[/bold magenta]")
        console.print(f"  [dim]Config file: {cfg.CONFIG_FILE}[/dim]\n")
        for k, v in current.items():
            display_value = _mask_secret(k, v)
            console.print(f"  [cyan]{k}[/cyan] = {display_value}")
        console.print()
        return

    if value is None:
        # Show one value
        current = cfg.load()
        if key in current:
            display_value = _mask_secret(key, current[key])
            console.print(f"  [cyan]{key}[/cyan] = {display_value}")
        else:
            console.print(f"  [red]Unknown key:[/red] {key}")
            console.print(f"  [dim]Available: {', '.join(cfg.DEFAULTS.keys())}[/dim]")
        return

    # Set value -- try to cast to the right type
    if key not in cfg.DEFAULTS:
        console.print(f"  [red]Unknown key:[/red] {key}")
        console.print(f"  [dim]Available: {', '.join(cfg.DEFAULTS.keys())}[/dim]")
        return

    default = cfg.DEFAULTS[key]
    if isinstance(default, int):
        value = int(value)
    elif isinstance(default, float):
        value = float(value)

    cfg.set_key(key, value)
    console.print(f"  [green]Set[/green] [cyan]{key}[/cyan] = {_mask_secret(key, value)}")


def _mask_secret(key: str, value) -> str:
    """Mask sensitive config values for display."""
    if "key" in key.lower() and isinstance(value, str) and len(value) > 8:
        return value[:4] + "..." + value[-4:]
    return str(value)


def _run_assistant(text_mode: bool = False, no_voice: bool = False, brain: Brain | None = None) -> None:
    """Main conversation loop."""
    ui = UI()
    settings = cfg.load()

    # --- Validate prerequisites ---
    if brain is None:
        brain = Brain(max_history=settings["max_history"])
    if not brain.available:
        ui.show_error(
            "The 'claude' CLI is not installed or not on your PATH.\n"
            "         Install it: https://docs.anthropic.com/en/docs/claude-cli"
        )
        sys.exit(1)

    # --- Initialize voice engine ---
    voice = VoiceEngine(
        fish_api_key=settings["fish_api_key"] if not no_voice else "",
        voice_model_id=settings["voice_model_id"],
        speech_speed=settings["speech_speed"],
        language=settings["language"],
        listen_timeout=settings["listen_timeout"],
        phrase_time_limit=settings["phrase_time_limit"],
    )

    # Warn about missing config
    if not text_mode and not voice.stt_available:
        ui.show_error(
            "SpeechRecognition or PyAudio not installed. "
            "Falling back to text mode.\n"
            "         Install: pip install SpeechRecognition PyAudio"
        )
        text_mode = True

    if not no_voice and not voice.tts_available:
        ui.show_info(
            "No Fish Audio API key configured. Running without voice output.\n"
            "         Set it: samantha config fish_api_key YOUR_KEY"
        )

    # Wire up activity callback so we can see what Claude is doing
    brain._activity_callback = lambda msg: ui.show_info(f"  {msg}")

    # Show models in use
    ui.show_info("Brain: Opus (thinking) → Haiku (voice summary) → Fish Audio (TTS)")

    # --- Start ---
    ui.show_welcome()

    try:
        _conversation_loop(ui, brain, voice, text_mode)
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        voice.cleanup()
        ui.show_goodbye()


def _conversation_loop(
    ui: UI,
    brain: Brain,
    voice: VoiceEngine,
    text_mode: bool,
) -> None:
    """Run the listen-think-speak loop until interrupted."""
    while True:
        # --- 1. Get user input ---
        if text_mode:
            try:
                user_input = ui.console.input("  [bold cyan]You:[/bold cyan] ").strip()
            except EOFError:
                break
            if not user_input:
                continue
        else:
            ui.show_status(Status.LISTENING)
            try:
                user_input = voice.listen()
            except KeyboardInterrupt:
                break
            except RuntimeError as e:
                ui.clear_status()
                ui.show_error(str(e))
                ui.show_info("Switching to text mode.")
                text_mode = True
                continue

            ui.clear_status()

            if user_input is None:
                continue  # Silence or unrecognized -- keep listening

            ui.show_user(user_input)

        # --- Natural language commands ---
        cmd = user_input.strip().lower()

        # Exit - only exact short commands or full phrases (not partial word matches)
        if cmd in ("exit", "quit", "bye", "goodbye", "stop", "/exit", "/q"):
            break
        exit_phrases = [
            "gotta go", "got to go", "i'm out", "i'm done", "wrap up",
            "talk later", "see you later", "see ya", "good night",
            "signing off", "peace out", "catch you later", "bye samantha",
            "bye bye", "that's all", "we're done", "samantha exit",
            "samantha quit", "samantha bye",
        ]
        if any(cmd == phrase for phrase in exit_phrases):
            break

        # Clear conversation
        if any(phrase in cmd for phrase in [
            "forget everything", "start over", "clear the conversation",
            "fresh start", "new conversation", "reset",
        ]) or cmd in ("/clear", "/c"):
            brain.history.clear()
            brain._first_sent = False
            brain._save_history()
            ui.show_info("Conversation cleared.")
            continue

        # --- 2. Think ---
        ui.show_status(Status.THINKING)
        try:
            response = brain.think(user_input)
        except (RuntimeError, TimeoutError) as e:
            ui.clear_status()
            ui.show_error(str(e))
            continue

        ui.clear_status()

        # --- 3. Respond ---
        # Show full Opus response if it was summarized
        full = getattr(brain, '_full_response', response)
        if full != response and len(full) > len(response):
            # Show the full Claude output in dim, then the spoken version
            from rich.text import Text
            from rich.panel import Panel
            ui.console.print(Panel(
                Text(full, style="dim"),
                title="[dim]Claude (Opus)[/]",
                border_style="dim",
                padding=(0, 1),
            ))

        if voice.tts_available and not text_mode:
            ui.show_status(Status.SPEAKING)
            try:
                import threading

                audio_path = voice.generate_audio(response)
                if audio_path:
                    player = threading.Thread(target=voice.play_audio, args=(audio_path,), daemon=True)
                    player.start()

                    ui.clear_status()
                    ui.show_samantha(response)

                    player.join()
                else:
                    ui.clear_status()
                    ui.show_samantha(response)
            except TTSError as e:
                ui.clear_status()
                ui.show_samantha(response)
                ui.show_info(f"Voice output failed: {e}")
        else:
            ui.show_samantha(response)

        ui.clear_status()


if __name__ == "__main__":
    main()
