"""Integration tests for MiniMax handler against the live API.

These tests require:
  - MINIMAX_API_KEY environment variable to be set
  - Network access to api.minimax.io

Run with:  pytest tests/test_minimax_integration.py -v
Skip with: pytest tests/ -v -k "not integration"
"""

import json
import os

import pytest

# Skip all tests if no API key is available
pytestmark = pytest.mark.skipif(
    not os.getenv("MINIMAX_API_KEY"),
    reason="MINIMAX_API_KEY not set",
)


@pytest.fixture
def minimax_client():
    """Create an OpenAI client configured for MiniMax."""
    from openai import OpenAI

    return OpenAI(
        base_url="https://api.minimax.io/v1",
        api_key=os.getenv("MINIMAX_API_KEY"),
    )


# ── Integration Test 1: Basic chat completion ────────────────────────────────
def test_minimax_chat_completion(minimax_client):
    """MiniMax API should return a valid chat completion."""
    response = minimax_client.chat.completions.create(
        model="MiniMax-M2.5",
        messages=[{"role": "user", "content": "Say hello in one word."}],
        temperature=0.01,
        max_tokens=10,
    )
    assert response.choices
    assert len(response.choices) > 0
    assert response.choices[0].message.content
    assert len(response.choices[0].message.content.strip()) > 0


# ── Integration Test 2: Function calling (tools) ─────────────────────────────
def test_minimax_function_calling(minimax_client):
    """MiniMax API should support OpenAI-compatible function calling."""
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name",
                        }
                    },
                    "required": ["location"],
                },
            },
        }
    ]

    response = minimax_client.chat.completions.create(
        model="MiniMax-M2.5",
        messages=[
            {"role": "user", "content": "What is the weather in San Francisco?"}
        ],
        tools=tools,
        temperature=0.01,
        max_tokens=200,
    )
    assert response.choices
    msg = response.choices[0].message
    # The model should either call the function or mention weather
    if msg.tool_calls:
        call = msg.tool_calls[0]
        assert call.function.name == "get_weather"
        args = json.loads(call.function.arguments)
        assert "location" in args


# ── Integration Test 3: Temperature=0 is accepted ────────────────────────────
def test_minimax_temperature_zero(minimax_client):
    """MiniMax API should accept temperature=0."""
    response = minimax_client.chat.completions.create(
        model="MiniMax-M2.5",
        messages=[{"role": "user", "content": "Reply with exactly: OK"}],
        temperature=0,
        max_tokens=5,
    )
    assert response.choices
    assert response.choices[0].message.content
