import random
import re


TOPIC_MAP = {
    "Python": [
        "Variables",
        "Data Types",
        "Conditions",
        "Loops",
        "Functions",
        "Lists",
        "Tuples",
        "Dictionaries",
        "OOP",
        "Exceptions",
    ],
    "SQL": [
        "SELECT",
        "WHERE",
        "ORDER BY",
        "GROUP BY",
        "HAVING",
        "JOIN",
        "Subqueries",
        "Aggregate Functions",
        "String Functions",
    ],
    "PostgreSQL": [
        "Data Types",
        "Constraints",
        "SELECT",
        "WHERE",
        "UPDATE",
        "DELETE",
        "JOIN",
        "GROUP BY",
        "ORDER BY",
        "ALTER TABLE",
        "String Functions",
    ],
    "DBMS": ["Normalization", "Transactions", "Indexes", "ER Model", "Concurrency"],
    "OOP": ["Classes", "Inheritance", "Polymorphism", "Encapsulation", "Abstraction"],
    "Data Structures": ["Arrays", "Linked Lists", "Stacks", "Queues", "Trees", "Graphs"],
    "Operating Systems": ["Processes", "Threads", "Scheduling", "Memory", "File Systems"],
    "Computer Networks": ["TCP/IP", "DNS", "Routing", "Sockets", "Security"],
}


def get_topics_for_subject(subject):
    return TOPIC_MAP.get(subject, [])


def get_default_quiz_length():
    return 10


def normalise_topic(topic):
    if not topic:
        return ""
    return topic.strip()


def normalize_question_text(question_text):
    return re.sub(r"\s+", " ", (question_text or "").strip().lower())


def choose_random_topic(subject):
    topics = get_topics_for_subject(subject)
    if not topics:
        return "General"
    return random.choice(topics)
