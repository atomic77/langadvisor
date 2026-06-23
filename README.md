# LangAdvisor

A Flet GUI application for grammar assessment and using local LLMs via Ollama.

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) running locally with a model available (e.g. `ollama pull llama3.2`)


## Development

To run the app locally - uv will automatically create a local virtual environment and pull down related dependencies:
   
```bash
   uv run main.py
```

## Project Structure

- `main.py` — Application entry point
- `core/` — Core logic (paths, services)
- `ui/` — Flet UI components
- `services/` — LLM integration via LangChain/Ollama
- `pyproject.toml` — Project configuration and dependencies
