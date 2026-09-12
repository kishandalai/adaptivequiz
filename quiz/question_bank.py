import json
import random
from pathlib import Path
from functools import lru_cache

from .utils import TOPIC_MAP, normalize_question_text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BANK_DIR = PROJECT_ROOT / "question_bank"
LEGACY_BANK_DIR = PROJECT_ROOT / "questions"
VALID_DIFFICULTIES = {"Easy", "Medium", "Hard"}
OPTION_IDS = ("A", "B", "C", "D")
TOPIC_ALIASES = {
    "Datatypes": "Data Types",
    "OOPS": "OOP",
    "SUB QUERY": "Subqueries",
    "Security in Computer Networks": "Security",
}


class QuestionBankError(ValueError):
    pass


def _validate_question(subject, topic, item, seen_ids, seen_texts):
    required = {"id", "question", "options", "correct_answer", "explanation", "difficulty"}
    optional = {"company", "year", "hint"}
    if not required.issubset(item) or set(item) - required - optional:
        raise QuestionBankError(f"Invalid fields for {subject}/{topic} question.")
    if not isinstance(item["id"], str) or not item["id"] or item["id"] in seen_ids:
        raise QuestionBankError(f"Duplicate or invalid question ID in {subject}/{topic}.")
    if not isinstance(item["question"], str) or not item["question"].strip():
        raise QuestionBankError(f"Question text is empty in {subject}/{topic}.")
    normalized = normalize_question_text(item["question"])
    if normalized in seen_texts:
        raise QuestionBankError(f"Duplicate question text in {subject}/{topic}.")
    if not isinstance(item["options"], dict) or tuple(item["options"]) != OPTION_IDS:
        raise QuestionBankError(f"Options must contain A, B, C, and D in {subject}/{topic}.")
    if len(set(item["options"].values())) != 4:
        raise QuestionBankError(f"Options must be unique in {subject}/{topic}.")
    if any(not isinstance(value, str) or not value.strip() for value in item["options"].values()):
        raise QuestionBankError(f"Empty option in {subject}/{topic}.")
    if item["correct_answer"] not in OPTION_IDS:
        raise QuestionBankError(f"Invalid correct answer in {subject}/{topic}.")
    if not isinstance(item["explanation"], str) or not item["explanation"].strip():
        raise QuestionBankError(f"Explanation is empty in {subject}/{topic}.")
    if item["difficulty"] not in VALID_DIFFICULTIES:
        raise QuestionBankError(f"Invalid difficulty in {subject}/{topic}.")
    seen_ids.add(item["id"])
    seen_texts.add(normalized)


@lru_cache(maxsize=1)
def load_question_bank():
    bank = {}
    for subject, topics in TOPIC_MAP.items():
        filename = f"{subject.lower().replace(' ', '_')}.json"
        path = BANK_DIR / filename
        if not path.exists():
            path = LEGACY_BANK_DIR / filename
        if not path.exists():
            raise QuestionBankError(f"Question bank file is missing for {subject}.")
        with path.open(encoding="utf-8") as file:
            data = json.load(file)
        if str(data.get("subject", "")).strip().lower() != subject.lower():
            raise QuestionBankError(f"Question bank topics do not match {subject}.")
        raw_topics = data.get("topics", {})
        normalized_topics = {}
        for raw_topic, questions in raw_topics.items():
            alias = TOPIC_ALIASES.get(raw_topic, raw_topic)
            canonical_topic = next(
                (topic for topic in topics if topic.lower() == alias.lower()),
                alias,
            )
            normalized_topics[canonical_topic] = questions
        if set(normalized_topics) != set(topics):
            raise QuestionBankError(f"Question bank topics do not match {subject}.")
        subject_questions = {}
        for topic in topics:
            questions = normalized_topics.get(topic)
            if not isinstance(questions, list) or len(questions) < 10:
                raise QuestionBankError(f"{subject}/{topic} must contain at least 10 questions.")
            seen_ids = set()
            seen_texts = set()
            for item in questions:
                _validate_question(subject, topic, item, seen_ids, seen_texts)
            if not any(item["difficulty"] == "Hard" for item in questions):
                medium_questions = [item for item in questions if item["difficulty"] == "Medium"]
                for item in medium_questions[-2:]:
                    item["difficulty"] = "Hard"
            subject_questions[topic] = {item["id"]: item for item in questions}
        bank[subject] = subject_questions
    return bank


def get_topic_questions(subject, topic):
    return load_question_bank()[subject][topic]


def get_bank_question(subject, topic, question_id):
    return get_topic_questions(subject, topic).get(question_id)


def select_question_ids(subject, topic, count=10):
    questions = get_topic_questions(subject, topic)
    if len(questions) < count:
        raise QuestionBankError(f"{subject}/{topic} does not contain enough questions.")
    return random.sample(list(questions), count)


def public_question(item):
    return {
        "id": item["id"],
        "question": item["question"],
        "options": [{"id": key, "text": item["options"][key]} for key in OPTION_IDS],
        "difficulty": item["difficulty"],
    }
