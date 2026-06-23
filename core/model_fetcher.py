"""Ollama model discovery."""

import ollama


def fetch_ollama_models() -> list[str]:
    """Return a sorted list of locally available Ollama model names."""
    models = ollama.list()
    return [m.model for m in sorted(models.models, key=lambda x: x.model)]
