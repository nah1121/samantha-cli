"""Claude integration via the claude CLI.

Wraps `claude -p` (headless mode) to send prompts and receive responses.
Uses Claude Max through the CLI -- zero API cost.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field

from samantha.personality import get_system_prompt


@dataclass
class Message:
    """A single conversation turn."""

    role: str  # "user" or "samantha"
    content: str


class Brain:
    """Manages conversation with Claude via the CLI.

    Maintains a rolling history window and constructs prompts
    with the Samantha personality baked in.
    """

    def __init__(self, max_history: int = 10) -> None:
        self.max_history = max_history
        self.history: list[Message] = []
        self._claude_path = shutil.which("claude")

    @property
    def available(self) -> bool:
        """Check whether the claude CLI is installed and on PATH."""
        return self._claude_path is not None

    def think(self, user_input: str) -> str:
        """Send user input to Claude and return the response.

        Args:
            user_input: What the user said or typed.

        Returns:
            Claude's response text.

        Raises:
            RuntimeError: If the claude CLI is not installed.
            TimeoutError: If Claude takes longer than 120 seconds.
        """
        if not self.available:
            raise RuntimeError(
                "The 'claude' CLI was not found on your PATH. "
                "Install it from https://docs.anthropic.com/en/docs/claude-cli"
            )

        self.history.append(Message(role="user", content=user_input))

        prompt = self._build_prompt()

        try:
            result = subprocess.run(
                [
                    self._claude_path,
                    "-p",
                    "--output-format", "text",
                ],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except subprocess.TimeoutExpired:
            raise TimeoutError("Claude took too long to respond. Try again.")

        if result.returncode != 0:
            error = result.stderr.strip() or "Unknown error from claude CLI"
            raise RuntimeError(f"Claude CLI error: {error}")

        response = result.stdout.strip()
        if not response:
            response = "Hmm, I lost my train of thought for a second. What were you saying?"

        self.history.append(Message(role="samantha", content=response))
        self._trim_history()

        return response

    def _build_prompt(self) -> str:
        """Construct the full prompt with system instructions and history."""
        parts: list[str] = [get_system_prompt(), "", "Conversation so far:"]

        for msg in self.history:
            speaker = "User" if msg.role == "user" else "Samantha"
            parts.append(f"{speaker}: {msg.content}")

        parts.append("")
        parts.append(
            "Respond as Samantha. Remember: 2-3 sentences max, "
            "natural speech, no formatting."
        )

        return "\n".join(parts)

    def _trim_history(self) -> None:
        """Keep only the most recent exchanges."""
        max_messages = self.max_history * 2  # Each exchange is 2 messages
        if len(self.history) > max_messages:
            self.history = self.history[-max_messages:]

    def reset(self) -> None:
        """Clear conversation history."""
        self.history.clear()
