from collections import defaultdict


DIFFICULTY_LEVELS = ["Easy", "Medium", "Hard"]
DIFFICULTY_INDEX = {name: index for index, name in enumerate(DIFFICULTY_LEVELS)}


def get_next_difficulty(current_level, recent_results):
    """Return the next difficulty after evaluating recent answers."""
    if current_level not in DIFFICULTY_INDEX:
        current_level = "Easy"

    if len(recent_results) < 2:
        return current_level

    consecutive_correct = 0
    consecutive_wrong = 0

    for is_correct in reversed(recent_results):
        if is_correct:
            consecutive_correct += 1
            consecutive_wrong = 0
        else:
            consecutive_wrong += 1
            consecutive_correct = 0

        if consecutive_correct >= 2:
            break
        if consecutive_wrong >= 2:
            break

    if consecutive_correct >= 2:
        return DIFFICULTY_LEVELS[min(DIFFICULTY_INDEX[current_level] + 1, len(DIFFICULTY_LEVELS) - 1)]
    if consecutive_wrong >= 2:
        return DIFFICULTY_LEVELS[max(DIFFICULTY_INDEX[current_level] - 1, 0)]
    return current_level


def calculate_accuracy(correct_answers, total_questions):
    if total_questions <= 0:
        return 0.0
    return round((correct_answers / total_questions) * 100, 2)


def get_skill_level(accuracy):
    if accuracy >= 80:
        return "Advanced"
    if accuracy >= 60:
        return "Proficient"
    if accuracy >= 40:
        return "Developing"
    return "Beginner"


def update_performance(topic_performance, is_correct):
    if topic_performance is None:
        topic_performance = {
            "total_questions": 0,
            "correct_answers": 0,
            "accuracy": 0.0,
            "current_level": "Easy",
        }

    topic_performance["total_questions"] += 1
    if is_correct:
        topic_performance["correct_answers"] += 1

    accuracy = calculate_accuracy(topic_performance["correct_answers"], topic_performance["total_questions"])
    topic_performance["accuracy"] = accuracy

    if accuracy >= 75:
        topic_performance["current_level"] = "Strong"
    elif accuracy < 50:
        topic_performance["current_level"] = "Weak"
    else:
        topic_performance["current_level"] = "Average"

    return topic_performance
