from __future__ import annotations

import json
from typing import Any


def _tool_name(tool: dict[str, Any]) -> str:
    fn = tool.get("function", tool)
    return str(fn.get("name", "tool"))


def _tool_text(tool: dict[str, Any]) -> str:
    fn = tool.get("function", tool)
    return " ".join(str(value) for value in (fn.get("name", ""), fn.get("description", "")) if value)


def _provider_group(name: str) -> str:
    clean = name.replace(".", "_")
    bits = [bit for bit in clean.split("_") if bit]
    if len(bits) <= 1:
        return clean
    if clean.startswith("GorillaFileSystem_"):
        return "GorillaFileSystem"
    if bits[0].lower().endswith("api"):
        return bits[0]
    return bits[0]


def _latest_user_text(messages: list[dict[str, Any]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            content = message.get("content", "")
            if isinstance(content, str):
                return content
            return json.dumps(content, sort_keys=True)
    return json.dumps(messages[-1] if messages else {}, sort_keys=True)


class BFCLToolRouter:
    """Deterministic AgentWeave-style router for BFCL-provided functions."""

    def __init__(self, max_provider_agents: int = 4, max_tools: int = 6,
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        if max_provider_agents < 1 or max_tools < 1:
            raise ValueError("routing budgets must be >= 1")
        self.max_provider_agents = max_provider_agents
        self.max_tools = max_tools
        self.embedding_model = embedding_model
        self._model = None

    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.embedding_model)
        return self._model

    def _similarities(self, query: str, texts: list[str]) -> list[float]:
        if not texts:
            return []
        vectors = self.model.encode([query] + texts, normalize_embeddings=True)
        return [float(vectors[0] @ vector) for vector in vectors[1:]]

    def select(self, messages: list[dict[str, Any]], functions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if len(functions) <= self.max_tools:
            return list(functions)

        query = _latest_user_text(messages)
        groups: dict[str, list[dict[str, Any]]] = {}
        for function in functions:
            groups.setdefault(_provider_group(_tool_name(function)), []).append(function)

        provider_names = sorted(groups)
        provider_scores = self._similarities(
            query, [" ".join(_tool_text(tool) for tool in groups[name]) for name in provider_names]
        )
        selected_provider_names = {
            name for name, _ in sorted(zip(provider_names, provider_scores), key=lambda x: (-x[1], x[0]))[:self.max_provider_agents]
        }
        selected = [tool for name in provider_names if name in selected_provider_names for tool in groups[name]]

        if len(selected) > self.max_tools:
            scores = self._similarities(query, [_tool_text(tool) for tool in selected])
            order = sorted(range(len(selected)), key=lambda idx: (-scores[idx], _tool_name(selected[idx])))
            selected = [selected[idx] for idx in order[:self.max_tools]]

        return selected or [functions[0]]


__all__ = ["BFCLToolRouter"]
