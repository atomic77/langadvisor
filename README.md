# LangAdvisor

A Flet GUI application for grammar assessment using local LLMs via Ollama.

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) running locally with a model available (e.g. `ollama pull llama3.2`)

## Setup

1. **Create a virtual environment and install dependencies**:
   ```bash
   uv venv
   source .venv/bin/activate
   uv sync
   ```

2. **Run the app**
   ```bash
   python main.py
   ```

## Project Structure

- `main.py` — Application entry point
- `core/` — Core logic (paths, services)
- `ui/` — Flet UI components
- `services/` — LLM integration via LangChain/Ollama
- `pyproject.toml` — Project configuration and dependencies
