import json
import os
import tempfile
import uuid
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.utils.text import slugify

from .learning_notes import get_languages
from .question_bank import BANK_DIR, LEGACY_BANK_DIR, TOPIC_ALIASES, load_question_bank
from .utils import TOPIC_MAP

COMPANY_CHOICES = (
    "General",
    "Amazon",
    "Google",
    "Microsoft",
    "Meta",
    "Apple",
    "TCS",
    "Infosys",
    "Wipro",
    "Other",
)


def _bank_path(subject):
    filename = f"{subject.lower().replace(' ', '_')}.json"
    path = BANK_DIR / filename
    return path if path.exists() else LEGACY_BANK_DIR / filename


def _read_bank(subject):
    path = _bank_path(subject)
    with path.open(encoding="utf-8") as file:
        return path, json.load(file)


def _write_bank(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_path = tempfile.mkstemp(dir=path.parent, suffix=".json")
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
            file.write("\n")
        os.replace(temporary_path, path)
    finally:
        if os.path.exists(temporary_path):
            os.unlink(temporary_path)
    load_question_bank.cache_clear()


def _storage_topic(document, topic):
    for raw_topic in document.get("topics", {}):
        if raw_topic == topic or TOPIC_ALIASES.get(raw_topic, raw_topic) == topic:
            return raw_topic
    return topic


def question_choices():
    return [(subject, subject) for subject in TOPIC_MAP]


def topic_choices():
    return sorted({topic for topics in TOPIC_MAP.values() for topic in topics})


def iter_questions():
    bank = load_question_bank()
    for subject, topics in bank.items():
        for topic, questions in topics.items():
            for item in questions.values():
                yield {
                    "subject": subject,
                    "topic": topic,
                    "id": item["id"],
                    "question": item["question"],
                    "options": item["options"],
                    "correct_answer": item["correct_answer"],
                    "explanation": item["explanation"],
                    "difficulty": item["difficulty"],
                    "company": item.get("company", "General"),
                    "year": item.get("year", ""),
                    "hint": item.get("hint", ""),
                }


def find_question(question_id):
    return next((item for item in iter_questions() if item["id"] == question_id), None)


def save_question(data, question_id=None):
    subject = data["subject"]
    topic = data["topic"]
    path, document = _read_bank(subject)
    topic = _storage_topic(document, topic)
    topics = document.setdefault("topics", {})
    questions = topics.setdefault(topic, [])
    question_fields = ("question", "options", "correct_answer", "explanation", "difficulty", "company", "year", "hint")
    record = {key: data[key] for key in question_fields if key in data}
    if question_id:
        for index, item in enumerate(questions):
            if item["id"] == question_id:
                questions[index] = {**item, **record, "id": question_id}
                break
        else:
            raise KeyError("Question does not exist")
    else:
        questions.append({**record, "id": f"admin_{uuid.uuid4().hex}"})
    _write_bank(path, document)


def delete_question(question_id):
    for subject in TOPIC_MAP:
        path, document = _read_bank(subject)
        for topic, questions in document.get("topics", {}).items():
            remaining = [item for item in questions if item.get("id") != question_id]
            if len(remaining) != len(questions):
                document["topics"][topic] = remaining
                _write_bank(path, document)
                return True
    return False


def note_payload(language_slug, topic):
    language = get_languages().get(language_slug)
    if not language or topic not in language["notes"]:
        return None
    return language["notes"][topic]


def note_rows():
    from .models import TechnicalNote

    stored = {(
        note.language_slug,
        note.topic,
    ): note for note in TechnicalNote.objects.all()}
    rows = []
    for language in get_languages().values():
        for topic_index, topic in enumerate(language["topics"]):
            rows.append({
                "language_slug": language["slug"],
                "language_name": language["name"],
                "topic": topic,
                "topic_index": topic_index,
                "stored": stored.get((language["slug"], topic)),
            })
    return rows
