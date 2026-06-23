"""LLM interaction layer."""

from httpx import ConnectError
from langchain_ollama import ChatOllama

_llm = None
_current_model = None
_default_model = None


def set_default_model(model: str | None) -> None:
    """Set the default model used when no explicit model is provided."""
    global _default_model
    _default_model = model.strip() if model else None


def get_default_model() -> str | None:
    """Return the currently configured default model."""
    return _default_model


def get_llm(model: str) -> ChatOllama:
    """Return a cached ChatOllama instance for the given model."""
    global _llm, _current_model
    resolved_model = (model or _default_model or "").strip()
    if not resolved_model:
        raise ValueError("No model configured. Choose a model or set a default model in Settings.")
    if _llm is None or _current_model != resolved_model:
        _llm = ChatOllama(model=resolved_model, temperature=0)
        _current_model = resolved_model
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
        feedback, suggestion = _parse_feedback_suggestion(content, language)
        if not feedback and not suggestion:
            feedback = content
        return feedback, suggestion
    except ConnectError:
        return "Cannot connect to Ollama.", ""
    except Exception as e:
        return f"Error: {e}", ""


def _parse_feedback_suggestion(content: str, language: str) -> tuple[str, str]:
    """Parse FEEDBACK:/SUGGESTION: blocks that may span multiple lines."""
    feedback = ""
    suggestion = ""
    current_field = None
    for line in content.splitlines():
        upper = line.upper()
        if upper.startswith("FEEDBACK:"):
            current_field = "feedback"
            feedback = line[len("FEEDBACK:") :].strip()
        elif upper.startswith("SUGGESTION:"):
            current_field = "suggestion"
            suggestion = line[len("SUGGESTION:") :].strip()
        elif current_field == "feedback":
            feedback = feedback + "\n" + line if feedback else line.strip()
        elif current_field == "suggestion":
            suggestion = suggestion + "\n" + line if suggestion else line.strip()
    return feedback.strip(), suggestion.strip()


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


_ECTS_LEVELS = {
    "A1": "Beginner - simple everyday phrases",
    "A2": "Elementary - routine tasks and social situations",
    "B1": "Intermediate - travel and work contexts",
    "B2": "Upper-Intermediate - complex topics and opinions",
    "C1": "Advanced - fluent and nuanced expression",
    "C2": "Proficient - near-native comprehension",
}


async def generate_practice_sentence(
    language: str, ects_level: str, formality: str, category: str, model: str
) -> tuple[str, str]:
    """Generate (phrase, english_translation) for practice at the given level."""
    if not language or not ects_level or not formality or not category:
        return "", ""
    level_desc = _ECTS_LEVELS.get(ects_level, ects_level)
    llm = get_llm(model)
    messages = [
        (
            "system",
            f"You are a translation practice generator. "
            f"The user is learning {language} at CEFR {ects_level} level ({level_desc}), "
            f"with {formality.lower()} register, focused on the category '{category}'. "
            f"Generate ONE short, natural {formality.lower()} {language} phrase or sentence "
            f"appropriate for this level and category. It should be something a learner at this stage "
            f"would be asked to translate INTO {language}. "
            "Also provide a concise English translation for learner help. "
            "Format your response exactly as:\n"
            "PHRASE: <the phrase in the target language>\n"
            "TRANSLATION: <the English translation>",
        ),
        (
            "human",
            f"Generate a {ects_level} level {formality.lower()} {language} phrase for translation practice in the category '{category}'.",
        ),
    ]
    try:
        result = await llm.ainvoke(messages)
        content = result.content.strip()
        phrase, translation = _parse_phrase_translation(content)
        if not phrase:
            phrase = content.strip()
        return phrase, translation
    except ConnectError:
        return "Cannot connect to Ollama.", ""
    except Exception as e:
        return f"Error: {e}", ""


async def check_translation(
    source_phrase: str,
    user_translation: str,
    language: str,
    formality: str,
    ects_level: str,
    model: str,
) -> str:
    """Return translation mistakes/explanation in English for the learner."""
    if not source_phrase.strip() or not user_translation.strip():
        return ""
    level_desc = _ECTS_LEVELS.get(ects_level, ects_level)
    llm = get_llm(model)
    messages = [
        (
            "system",
            f"You are an English language tutor. "
            f"The learner is at CEFR {ects_level} level ({level_desc}), "
            f"translating from {language} into English, with {formality.lower()} register. "
            "The learner has provided an English translation of the original phrase. "
            "Assess the accuracy of the translation: does it faithfully convey the meaning "
            "of the original phrase? Identify any errors in meaning, word choice, register, or naturalness. "
            "Include a corrected English version when needed. "
            "Format your response exactly as:\n"
            "MISTAKES: <translation errors and what the correct English would be>",
        ),
        (
            "human",
            f"Original phrase ({language}, {formality.lower()}): {source_phrase}\n\n"
            f"Learner's English translation: {user_translation}",
        ),
    ]
    try:
        result = await llm.ainvoke(messages)
        content = result.content.strip()
        mistakes = _parse_mistakes(content)
        return mistakes or content
    except ConnectError:
        return "Cannot connect to Ollama."
    except Exception as e:
        return f"Error: {e}"


def _parse_phrase_translation(content: str) -> tuple[str, str]:
    """Parse PHRASE:/TRANSLATION: blocks that may span multiple lines."""
    phrase = ""
    translation = ""
    current_field = None
    for line in content.splitlines():
        upper = line.upper()
        if upper.startswith("PHRASE:"):
            current_field = "phrase"
            phrase = line[len("PHRASE:") :].strip()
        elif upper.startswith("TRANSLATION:"):
            current_field = "translation"
            translation = line[len("TRANSLATION:") :].strip()
        elif current_field == "phrase":
            phrase = phrase + "\n" + line if phrase else line.strip()
        elif current_field == "translation":
            translation = translation + "\n" + line if translation else line.strip()
    return phrase.strip(), translation.strip()


def _parse_mistakes(content: str) -> str:
    """Parse a MISTAKES: block that may span multiple lines."""
    mistakes = ""
    in_mistakes = False
    for line in content.splitlines():
        upper = line.upper()
        if upper.startswith("MISTAKES:"):
            in_mistakes = True
            mistakes = line[len("MISTAKES:") :].strip()
        elif in_mistakes:
            mistakes = mistakes + "\n" + line if mistakes else line.strip()
    return mistakes.strip()
