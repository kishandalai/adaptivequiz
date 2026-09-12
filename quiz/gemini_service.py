import json
import logging
import time
from typing import Any

from django.conf import settings
from google import genai

logger = logging.getLogger(__name__)
_gemini_disabled_until = 0


def _fallback_question(subject, topic, difficulty, excluded_questions=None):
    """Keep the quiz usable when Gemini is unavailable or rate-limited."""
    variants = [
        f"Which statement best describes {topic} in {subject}?",
        f"What is the main learning focus of {topic} in {subject}?",
        f"Which option is most closely related to {topic} in {subject}?",
    ]
    excluded_questions = excluded_questions or []
    question_text = next(
        (variant for variant in variants if variant not in excluded_questions),
        f"Practice question about {topic} in {subject} ({len(excluded_questions) + 1})",
    )
    return {
        "success": True,
        "question": {
            "question": question_text,
            "options": [
                f"The core concepts and practical use of {topic}",
                "An unrelated subject area",
                "A database credential",
                "A user interface color",
            ],
            "correct_answer": f"The core concepts and practical use of {topic}",
            "explanation": f"This option best describes the purpose and practical focus of {topic} in {subject}.",
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
        },
    }


def _validate_generated_question(data: Any):
    if not isinstance(data, dict):
        raise ValueError("Gemini response is not a JSON object.")

    question = data.get("question")
    options = data.get("options")
    correct_answer = data.get("correct_answer")
    explanation = data.get("explanation")
    subject = data.get("subject")
    topic = data.get("topic")
    difficulty = data.get("difficulty")

    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question text is missing or invalid.")
    if not isinstance(options, list) or len(options) != 4:
        raise ValueError("A question must include exactly four options.")
    if len(set(options)) != 4:
        raise ValueError("Options contain duplicates.")
    if not all(isinstance(item, str) and item.strip() for item in options):
        raise ValueError("Each option must be a non-empty string.")
    if not isinstance(correct_answer, str) or correct_answer not in options:
        raise ValueError("Correct answer must match one of the options.")
    if not isinstance(explanation, str) or not explanation.strip():
        raise ValueError("Explanation is missing.")
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("Subject is missing.")
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("Topic is missing.")
    if not isinstance(difficulty, str) or difficulty not in {"Easy", "Medium", "Hard"}:
        raise ValueError("Difficulty is invalid.")

    return {
        "question": question.strip(),
        "options": [item.strip() for item in options],
        "correct_answer": correct_answer.strip(),
        "explanation": explanation.strip(),
        "subject": subject.strip(),
        "topic": topic.strip(),
        "difficulty": difficulty,
    }

def generate_question(subject, topic, difficulty, excluded_questions=None):
    """Call the Gemini API and return a validated question payload."""
    global _gemini_disabled_until
    if time.time() < _gemini_disabled_until:
        return _fallback_question(subject, topic, difficulty, excluded_questions)

    api_key = getattr(settings, "GEMINI_API_KEY", "")
    if not api_key:
        return _fallback_question(subject, topic, difficulty, excluded_questions)

    try:
        client = genai.Client(api_key=api_key)
        model_name = getattr(settings, "GEMINI_MODEL", "gemini-3.6-flash")
        excluded_questions = [item for item in (excluded_questions or []) if item]
        exclusion_instruction = ""
        if excluded_questions:
            exclusion_instruction = (
                "Do not repeat or paraphrase any of these questions: "
                + json.dumps(excluded_questions)
                + ". "
            )
        prompt = (
            "You are generating exactly one multiple-choice question for a student quiz. "
            "Return only valid JSON with this structure: "
            "{\"question\": \"Question text\", \"options\": [\"Option 1\", \"Option 2\", \"Option 3\", \"Option 4\"], \"correct_answer\": \"Option 2\", \"explanation\": \"Explanation\", \"subject\": \"Python\", \"topic\": \"Functions\", \"difficulty\": \"Medium\"}. "
            "Ensure there are exactly 4 options, no duplicates, exactly one correct answer, and no extra text outside JSON. "
            "The question must match the subject and topic and difficulty exactly. "
            + exclusion_instruction
            + f"Requested subject: {subject}; requested topic: {topic}; requested difficulty: {difficulty}."
        )
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )

        text = getattr(response, "text", None)
        if not text:
            return {"success": False, "message": "Gemini returned an empty response."}

        payload = json.loads(text)
        validated = _validate_generated_question(payload)

        if validated["subject"].lower() != str(subject).lower():
            raise ValueError("Question subject does not match the requested subject.")
        if validated["topic"].lower() != str(topic).lower():
            raise ValueError("Question topic does not match the requested topic.")
        if validated["difficulty"] != difficulty:
            raise ValueError("Question difficulty does not match the requested difficulty.")

        return {"success": True, "question": validated}
    except json.JSONDecodeError:
        logger.exception("Gemini returned invalid JSON.")
        return _fallback_question(subject, topic, difficulty, excluded_questions)
    except Exception as exc:
        logger.warning("Gemini unavailable; using local fallback question: %s", exc)
        _gemini_disabled_until = time.time() + 300
        return _fallback_question(subject, topic, difficulty, excluded_questions)
