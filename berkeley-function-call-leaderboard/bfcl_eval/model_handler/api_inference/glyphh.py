"""
Gorilla-compatible handler for BFCL leaderboard submission.

Decodes pre-computed result files into AST/execute formats expected
by the gorilla eval framework. Pure HDC model — no LLM API calls.

Result format by category:
  Single-turn (AST):  result = '[{"func_name": {"param": "val"}}]'  (JSON string)
  Irrelevance:        result = ''  (empty string → no function call)
  Multi-turn:         result = [["[{...}]"], ["[{...}]"]]  (list[list[str]])
  Memory (agentic):   result = 'retrieved text...'  (plain text)

Integration:
  1. Copy this file into gorilla repo's model_handler/api_inference/ directory
  2. Register in model_config.py as a ModelConfig entry
  3. Add to SUPPORTED_MODELS
  4. Place result files in result/glyphh-hdc-v1/<group>/

See: https://github.com/ShishirPatil/gorilla/blob/main/berkeley-function-call-leaderboard/CONTRIBUTING.md
"""

from __future__ import annotations

import json
from typing import Any


class GlyphhHDCHandler:
    """Gorilla-compatible handler for Glyphh HDC model.

    Decodes pre-computed results — no inference (pure HDC, not an LLM).
    Only decode_ast() and decode_execute() are needed for evaluation.
    """

    def __init__(self, **kwargs: Any) -> None:
        pass

    # ── Decode: AST format ────────────────────────────────────────────────

    def decode_ast(
        self,
        result: Any,
        language: str = "Python",
        has_tool_call_tag: bool = False,
    ) -> list[dict]:
        """Convert result to AST format: [{"func_name": {"param": val}}].

        Handles:
          - JSON string: parse into list of function call dicts
          - Already a list: return as-is
          - Empty/unparseable: return [] (treated as "no function call")
        """
        if isinstance(result, list):
            return result

        if not isinstance(result, str) or not result.strip():
            return []

        try:
            parsed = json.loads(result)
            if isinstance(parsed, list):
                return parsed
            return []
        except (json.JSONDecodeError, TypeError):
            return []

    # ── Decode: Execute format ────────────────────────────────────────────

    def decode_execute(
        self,
        result: Any,
        has_tool_call_tag: bool = False,
    ) -> list[str]:
        """Convert result to execute format: ["func_name(param=val, ...)"].

        Handles:
          - JSON string of [{func: {args}}] → ["func(k=v, ...)"]
          - Already a list of strings: return as-is
          - Empty/unparseable: return []
        """
        if isinstance(result, list):
            # Already decoded (e.g. list of executable strings)
            if all(isinstance(s, str) for s in result):
                return result
            # List of dicts — convert to executable strings
            return self._dicts_to_exec(result)

        if not isinstance(result, str) or not result.strip():
            return []

        try:
            parsed = json.loads(result)
            if isinstance(parsed, list):
                return self._dicts_to_exec(parsed)
            return []
        except (json.JSONDecodeError, TypeError):
            return []

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _dicts_to_exec(calls: list) -> list[str]:
        """Convert [{func: {param: val}}, ...] to ["func(param=val)", ...]."""
        result = []
        for call in calls:
            if not isinstance(call, dict):
                continue
            for func_name, params in call.items():
                # Handle JSON-stringified params (e.g. '{"folder": "workspace"}')
                if isinstance(params, str):
                    try:
                        params = json.loads(params)
                    except (json.JSONDecodeError, TypeError):
                        pass
                if not isinstance(params, dict) or not params:
                    result.append(f"{func_name}()")
                else:
                    args = ", ".join(f"{k}={repr(v)}" for k, v in params.items())
                    result.append(f"{func_name}({args})")
        return result
