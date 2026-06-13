"""
Anthropic API wrapper — single reusable client for all routers.

Every Claude call in the codebase goes through this module so we have
one place to change model, max_tokens, or error handling.
"""

import os

import anthropic

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key or api_key == "your_key_here":
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. "
                "Copy .env.example to .env and add your real key."
            )
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def call_claude(system_prompt: str, user_message: str, max_tokens: int = 1000) -> str:
    """Send a message to Claude and return the text response."""
    client = _get_client()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


def call_claude_with_image(
    system_prompt: str,
    user_text: str,
    image_base64: str,
    media_type: str = "image/png",
    max_tokens: int = 2000,
) -> str:
    """Send a message with an image attachment to Claude."""
    client = _get_client()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_base64,
                        },
                    },
                    {"type": "text", "text": user_text},
                ],
            }
        ],
    )
    return response.content[0].text
