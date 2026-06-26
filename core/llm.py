"""LLM interaction layer."""

import re

from httpx import ConnectError
from langchain_ollama import ChatOllama

_llm = None
_current_model = None
_default_model = None

PracticePhrase = tuple[str, str] | tuple[str, str, str]

_ROMANIZATION_SCHEMES = {
    "Mandarin Chinese": "Hanyu Pinyin with tone marks",
    "Hindi": "IAST",
    "Bengali": "IAST or ISO 15919",
    "Russian": "ISO 9 or a widely recognized Russian romanization",
    "Japanese": "modified Hepburn",
    "Punjabi": "IAST or ISO 15919",
    "Marathi": "IAST or ISO 15919",
    "Telugu": "IAST or ISO 15919",
    "Korean": "Revised Romanization of Korean",
    "Tamil": "ISO 15919",
    "Urdu": "ALA-LC or a widely recognized Urdu romanization",
    "Egyptian Arabic": "a standard Arabic romanization such as DIN 31635 or ALA-LC",
    "Gujarati": "IAST or ISO 15919",
    "Iranian Persian": "a standard Persian romanization such as ALA-LC",
    "Kannada": "ISO 15919",
    "Malayalam": "ISO 15919",
    "Odia": "ISO 15919",
    "Ukrainian": "the Ukrainian national transliteration system",
    "Arabic (Modern Standard)": "a standard Arabic romanization such as DIN 31635 or ALA-LC",
    "Sindhi": "ISO 15919 or a widely recognized Sindhi romanization",
    "Amharic": "a standard Ethiopic romanization",
    "Armenian": "ISO 9985",
    "Belarusian": "BGN/PCGN or a widely recognized Belarusian romanization",
    "Bulgarian": "the official Bulgarian transliteration system",
    "Georgian": "the Georgian national romanization system",
    "Greek": "ELOT 743",
    "Macedonian": "ISO 9 or a widely recognized Macedonian romanization",
    "Serbian": "Serbian Latin script when the generated phrase is Cyrillic",
    "Avestan": "a standard scholarly Avestan transliteration",
    "Classical Armenian": "ISO 9985 or a standard scholarly Armenian transliteration",
    "Classical Sanskrit": "IAST",
    "Vedic Sanskrit": "IAST",
    "Old Persian": "a standard scholarly Old Persian transliteration",
    "Ancient Greek": "ISO 843 or a standard scholarly Greek transliteration",
    "Mycenaean Greek": "a standard Linear B transliteration",
    "Gothic": "a standard scholarly Gothic transliteration",
    "Old Church Slavonic": "ISO 9 or a standard scholarly Old Church Slavonic transliteration",
    "Old East Slavic": "ISO 9 or a standard scholarly Old East Slavic transliteration",
    "Old Japanese": "a standard scholarly Old Japanese romanization",
    "Classical Japanese": "modified Hepburn or a standard scholarly classical Japanese romanization",
    "Kanbun": "modified Hepburn for Japanese reading or Pinyin for Chinese reading, whichever fits the generated text",
    "Old Chinese": "Baxter-Sagart or another standard scholarly Old Chinese reconstruction",
    "Middle Chinese": "Baxter notation or another standard scholarly Middle Chinese reconstruction",
    "Classical Chinese": "Hanyu Pinyin or the standard romanization for the selected reading tradition",
    "Literary Chinese": "Hanyu Pinyin or the standard romanization for the selected reading tradition",
    "Old Korean": "Yale romanization or a standard scholarly Old Korean transliteration",
    "Middle Korean": "Yale romanization",
    "Old Tibetan": "Wylie transliteration",
    "Classical Tibetan": "Wylie transliteration",
    "Tangut": "a standard scholarly Tangut reconstruction or transliteration",
    "Khitan": "a standard scholarly Khitan transliteration",
    "Jurchen": "a standard scholarly Jurchen transliteration",
    "Classical Mongolian": "Mongolian transliteration or a standard scholarly romanization",
    "Old Vietnamese": "a standard scholarly Old Vietnamese reconstruction or romanization",
}


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
    language: str,
    ects_level: str,
    formality: str,
    category: str,
    model: str,
    include_romanization: bool = False,
) -> PracticePhrase:
    """Generate a phrase for practice at the given level."""
    if not language or not ects_level or not formality or not category:
        return ("", "", "") if include_romanization else ("", "")
    level_desc = _ECTS_LEVELS.get(ects_level, ects_level)
    llm = get_llm(model)
    romanization_instruction = (
        f" {_romanization_instruction(language)} " if include_romanization else " "
    )
    response_format = (
        "PHRASE: <the phrase in the target language>\n"
        "TRANSLATION: <the English translation>"
    )
    if include_romanization:
        response_format += "\nROMANIZATION: <standard romanization/latinization, or blank>"
    messages = [
        (
            "system",
            f"You are a translation practice generator. "
            f"The user is learning {language} at CEFR {ects_level} level ({level_desc}), "
            f"with {formality.lower()} register, focused on the category '{category}'. "
            f"Generate ONE short, natural {formality.lower()} {language} phrase or sentence "
            f"appropriate for this level and category. It should be something a learner at this stage "
            f"would be asked to translate INTO {language}. "
            "For languages normally written in non-Latin scripts, write PHRASE in "
            "the original script, not as a romanization. "
            "Also provide a concise English translation for learner help. "
            f"{romanization_instruction}"
            "Format your response exactly as:\n"
            f"{response_format}",
        ),
        (
            "human",
            f"Generate a {ects_level} level {formality.lower()} {language} phrase for translation practice in the category '{category}'.",
        ),
    ]
    try:
        result = await llm.ainvoke(messages)
        content = result.content.strip()
        parsed = _parse_phrase_translation(content, include_romanization)
        phrase = parsed[0]
        if not phrase:
            phrase = content.strip()
            if include_romanization:
                return phrase, "", ""
            return phrase, ""
        return parsed
    except ConnectError:
        return (
            ("Cannot connect to Ollama.", "", "")
            if include_romanization
            else ("Cannot connect to Ollama.", "")
        )
    except Exception as e:
        return (f"Error: {e}", "", "") if include_romanization else (f"Error: {e}", "")


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


def _romanization_instruction(language: str) -> str:
    """Return prompt guidance for optional Latinization generation."""
    scheme = _ROMANIZATION_SCHEMES.get(language)
    if scheme:
        return (
            f"When the generated phrase is written in a non-Latin script, also provide "
            f"its standard romanization using {scheme}. If the phrase is already in "
            "Latin script, leave ROMANIZATION blank."
        )
    return (
        "If the target phrase is normally written in a non-Latin script and a widely "
        "accepted romanization/latinization standard exists, include that standard "
        "romanization. If the language normally uses Latin script or no standard "
        "exists, leave ROMANIZATION blank."
    )


def _parse_phrase_translation(
    content: str, include_romanization: bool = False
) -> PracticePhrase:
    """Parse PHRASE:/TRANSLATION:/ROMANIZATION: blocks that may span multiple lines."""
    phrase = ""
    translation = ""
    romanization = ""
    current_field = None
    for line in content.splitlines():
        upper = line.upper()
        if upper.startswith("PHRASE:"):
            current_field = "phrase"
            phrase = line[len("PHRASE:") :].strip()
        elif upper.startswith("TRANSLATION:"):
            current_field = "translation"
            translation = line[len("TRANSLATION:") :].strip()
        elif upper.startswith("ROMANIZATION:"):
            current_field = "romanization"
            romanization = line[len("ROMANIZATION:") :].strip()
        elif current_field == "phrase":
            phrase = phrase + "\n" + line if phrase else line.strip()
        elif current_field == "translation":
            translation = translation + "\n" + line if translation else line.strip()
        elif current_field == "romanization":
            romanization = romanization + "\n" + line if romanization else line.strip()
    if include_romanization:
        return phrase.strip(), translation.strip(), romanization.strip()
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


async def generate_practice_set(
    language: str,
    ects_level: str,
    formality: str,
    category: str,
    count: int,
    model: str,
    include_romanization: bool = False,
) -> list[PracticePhrase]:
    """Generate `count` distinct practice phrases for a Lesson round.

    Returns two-field phrase tuples by default, or three-field tuples with
    romanization when requested. On error, returns an error phrase tuple.
    """
    if not language or not ects_level or not formality or not category or count <= 0:
        return []
    level_desc = _ECTS_LEVELS.get(ects_level, ects_level)
    llm = get_llm(model)
    romanization_instruction = (
        f" {_romanization_instruction(language)} " if include_romanization else " "
    )
    item_format = (
        f"1. PHRASE: <phrase in target language>\n"
        f"   TRANSLATION: <english translation>\n"
    )
    second_item_format = (
        f"2. PHRASE: <phrase in target language>\n"
        f"   TRANSLATION: <english translation>\n"
    )
    if include_romanization:
        item_format += "   ROMANIZATION: <standard romanization/latinization, or blank>\n"
        second_item_format += (
            "   ROMANIZATION: <standard romanization/latinization, or blank>\n"
        )
    messages = [
        (
            "system",
            f"You are a translation practice generator. "
            f"The user is learning {language} at CEFR {ects_level} level ({level_desc}), "
            f"with {formality.lower()} register, focused on the category '{category}'. "
            f"Generate {count} DISTINCT short, natural {formality.lower()} {language} "
            f"phrases or sentences appropriate for this level and category. "
            f"They should be things a learner at this stage would be asked to translate "
            f"into English. Each phrase should be unique in meaning and vocabulary. "
            "For languages normally written in non-Latin scripts, write PHRASE in "
            "the original script, not as a romanization. "
            f"For each, also provide a concise English translation for learner help. "
            f"{romanization_instruction}"
            f"Format your response exactly as a numbered list:\n"
            f"{item_format}"
            f"{second_item_format}"
            f"... and so on up to {count}. Do not add any commentary before or after the list.",
        ),
        (
            "human",
            f"Generate {count} {ects_level} level {formality.lower()} {language} phrases "
            f"for translation practice in the category '{category}'.",
        ),
    ]
    try:
        result = await llm.ainvoke(messages)
        content = result.content.strip()
        return _parse_practice_set(content, count, include_romanization)
    except ConnectError:
        return (
            [("Cannot connect to Ollama.", "", "")]
            if include_romanization
            else [("Cannot connect to Ollama.", "")]
        )
    except Exception as e:
        return [(f"Error: {e}", "", "")] if include_romanization else [(f"Error: {e}", "")]


async def grade_practice_batch(
    items: list[tuple[str, str, str]],
    language: str,
    formality: str,
    ects_level: str,
    model: str,
) -> tuple[str, list[dict]]:
    """Grade a batch of learner translations in a single LLM call.

    `items` is a list of (phrase, user_answer, reference_translation).
    Returns (overall_summary, results) where each result dict has
    {phrase, user_answer, reference, score (0-10), mistakes, better}.
    """
    if not items:
        return "", []
    level_desc = _ECTS_LEVELS.get(ects_level, ects_level)
    llm = get_llm(model)
    blocks = []
    for i, (phrase, user_answer, _reference) in enumerate(items, start=1):
        blocks.append(
            f"{i}. ORIGINAL ({language}, {formality.lower()}): {phrase}\n"
            f"   LEARNER ANSWER: {user_answer or '(no answer)'}"
        )
    numbered = "\n\n".join(blocks)
    messages = [
        (
            "system",
            f"You are an English language tutor grading a batch of translations. "
            f"The learner is at CEFR {ects_level} level ({level_desc}), "
            f"translating from {language} into English, with {formality.lower()} register. "
            f"The user may not have access to a keyboard with diacritics or accents, "
            f"so please do your best to interpret these based on the closest English "
            f"latin character approximation. "
            f"For EACH numbered item, score the translation from 0 to 10 (10 = perfect) "
            f"based on meaning, word choice, register, and naturalness. "
            f"Identify any errors and suggest a better English translation. "
            f"Then provide one OVERALL summary line at the end. "
            f"Format your response exactly as:\n"
            f"1. SCORE: <0-10> | MISTAKES: <errors and what would be correct> | BETTER: <ideal English>\n"
            f"2. SCORE: <0-10> | MISTAKES: ... | BETTER: ...\n"
            f"... and so on for every item.\n"
            f"OVERALL: <X>/<max> | SUMMARY: <one-paragraph summary of strengths and weaknesses>",
        ),
        (
            "human",
            f"Grade these {len(items)} translations:\n\n{numbered}",
        ),
    ]
    try:
        result = await llm.ainvoke(messages)
        content = result.content.strip()
        return _parse_grade_batch(content, items)
    except ConnectError:
        return ("Cannot connect to Ollama.", [])
    except Exception as e:
        return (f"Error: {e}", [])


def _parse_practice_set(
    content: str, expected_count: int, include_romanization: bool = False
) -> list[PracticePhrase]:
    """Parse a numbered PHRASE/TRANSLATION/ROMANIZATION list from model output."""
    fields = "PHRASE|TRANSLATION|ROMANIZATION"
    numbered = re.compile(rf"^\s*(\d+)\.\s*({fields})\s*:\s*(.*)$", re.IGNORECASE)
    unnumbered = re.compile(rf"^\s*({fields})\s*:\s*(.*)$", re.IGNORECASE)
    by_index: dict[int, dict[str, str]] = {}
    current_idx: int | None = None
    current_field: str | None = None
    for line in content.splitlines():
        m = numbered.match(line)
        if m:
            idx = int(m.group(1))
            field = m.group(2).lower()
            value = m.group(3).strip()
            slot = by_index.setdefault(
                idx, {"phrase": "", "translation": "", "romanization": ""}
            )
            slot[field] = value
            current_idx = idx
            current_field = field
            continue
        u = unnumbered.match(line)
        if u and current_idx is not None:
            field = u.group(1).lower()
            value = u.group(2).strip()
            slot = by_index.setdefault(
                current_idx, {"phrase": "", "translation": "", "romanization": ""}
            )
            slot[field] = value
            current_field = field
            continue
        # Continuation line - attach to the most recent (index, field).
        if current_idx is not None and current_field is not None and line.strip():
            slot = by_index.setdefault(
                current_idx, {"phrase": "", "translation": "", "romanization": ""}
            )
            existing = slot.get(current_field, "")
            slot[current_field] = (
                (existing + "\n" + line.strip()).strip() if existing else line.strip()
            )
    out: list[PracticePhrase] = []
    for i in range(1, expected_count + 1):
        slot = by_index.get(i)
        if slot is None:
            continue
        phrase = slot.get("phrase", "").strip()
        translation = slot.get("translation", "").strip()
        romanization = slot.get("romanization", "").strip()
        if phrase:
            if include_romanization:
                out.append((phrase, translation, romanization))
            else:
                out.append((phrase, translation))
    return out


def _parse_grade_batch(
    content: str, items: list[tuple[str, str, str]]
) -> tuple[str, list[dict]]:
    """Parse a numbered SCORE/MISTAKES/BETTER list with an optional OVERALL line."""
    line_pattern = re.compile(
        r"^\s*(\d+)\.\s*SCORE\s*:\s*([^|]*?)\s*\|\s*MISTAKES\s*:\s*(.*?)\s*\|\s*BETTER\s*:\s*(.*)$",
        re.IGNORECASE,
    )
    overall_pattern = re.compile(
        r"^\s*OVERALL\s*:\s*([^|]*?)\s*\|\s*SUMMARY\s*:\s*(.*)$", re.IGNORECASE
    )
    results: dict[int, dict] = {}
    summary = ""
    for line in content.splitlines():
        m_overall = overall_pattern.match(line)
        if m_overall:
            summary = m_overall.group(2).strip()
            continue
        m = line_pattern.match(line)
        if m:
            idx = int(m.group(1))
            raw_score = m.group(2).strip()
            try:
                score = max(0, min(10, int(raw_score.split()[0])))
            except (ValueError, IndexError):
                score = 0
            results[idx] = {
                "score": score,
                "mistakes": m.group(3).strip(),
                "better": m.group(4).strip(),
            }
    # Merge results with the input items, filling in defaults for missing indices.
    out: list[dict] = []
    for i, (phrase, user_answer, reference) in enumerate(items, start=1):
        r = results.get(i)
        if r is None:
            out.append({
                "phrase": phrase,
                "user_answer": user_answer,
                "reference": reference,
                "score": 0,
                "mistakes": "Not answered." if not user_answer.strip() else "Not graded.",
                "better": reference,
            })
        else:
            out.append({
                "phrase": phrase,
                "user_answer": user_answer,
                "reference": reference,
                "score": r["score"],
                "mistakes": r["mistakes"],
                "better": r["better"],
            })
    return summary, out
