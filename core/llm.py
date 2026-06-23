"""LLM interaction layer."""

from httpx import ConnectError
from langchain_ollama import ChatOllama

_llm = None
_current_model = None


def get_llm(model: str) -> ChatOllama:
    """Return a cached ChatOllama instance for the given model."""
    global _llm, _current_model
    if _llm is None or _current_model != model:
        _llm = ChatOllama(model=model, temperature=0)
        _current_model = model
    return _llm


async def get_feedback_and_suggestion(
    text: str, language: str, formality: str, model: str
) -> tuple[str, str]:
    """Get feedback and a suggested correction for grammatically incorrect text."""
    llm = get_llm(model)
    messages = [
        (
            "system",
            f"You are a {formality.lower()} grammar tutor for {language}. "
            f"The user will provide a sentence in {language}. "
            "Provide feedback on any grammatical errors, then a corrected version. "
            "Also grade the sentence on the likely degree of intelligibilty for a native speaker. "
            "The user may not have access to a keyboard with diacritics or accents, so please do your best to interpret these based on the closest English latin character approximation."
            "Always provide your feedback in English. "
            "Format your response exactly as:\n"
            "FEEDBACK: <your feedback in English>\n"
            "SUGGESTION: <corrected {language} sentence>",
        ),
        ("human", text),
    ]
    try:
        result = await llm.ainvoke(messages)
        content = result.content.strip()
        feedback = ""
        suggestion = ""
        for line in content.splitlines():
            if line.startswith("FEEDBACK:"):
                feedback = line[len("FEEDBACK:") :].strip()
            elif line.startswith("SUGGESTION:"):
                suggestion = line[len("SUGGESTION:") :].strip()
        if not feedback and not suggestion:
            feedback = content
        return feedback, suggestion
    except ConnectError:
        return "Cannot connect to Ollama.", ""
    except Exception as e:
        return f"Error: {e}", ""


async def check_grammar(
    text: str, language: str, formality: str, model: str
) -> tuple[str, str, str]:
    """Return (verdict, feedback, suggestion). Verdict is 'yes', 'no', or error string."""
    if not text.strip():
        return "", "", ""
    llm = get_llm(model)
    messages = [
        (
            "system",
            f"You are a {formality.lower()} grammar checker for {language}. "
            f"Assess the following {language} sentence for grammatical errors with {formality.lower()} appropriateness. "
            "Respond only 'yes' if the sentence is grammatically correct, 'no' if it is not.",
        ),
        ("human", text),
    ]
    try:
        result = await llm.ainvoke(messages)
        verdict = result.content.strip().lower()
        if verdict not in ("yes", "no"):
            verdict = "yes" if "yes" in verdict else "no"
        feedback, suggestion = (
            await get_feedback_and_suggestion(text, language, formality, model)
            if verdict == "no"
            else ("", "")
        )
        return verdict, feedback, suggestion
    except ConnectError:
        return "error: cannot connect to Ollama.", "", ""
    except Exception as e:
        return f"error: {e}", "", ""
