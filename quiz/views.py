import json
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from .adaptive_engine import calculate_accuracy, get_skill_level
from .forms import LoginForm, QuizSelectionForm, RegistrationForm
from .gemini_service import generate_question
from .learning_notes import LANGUAGES, LANGUAGE_DEFINITIONS, all_search_items
from .models import AnswerRecord, Question, QuizAttempt, TopicPerformance
from .question_bank import QuestionBankError, get_bank_question, load_question_bank, select_question_ids
from .utils import get_topics_for_subject, get_default_quiz_length, normalize_question_text


SUPPORTED_SUBJECTS = [
    "Python",
    "SQL",
    "PostgreSQL",
    "DBMS",
    "OOP",
    "Data Structures",
    "Operating Systems",
    "Computer Networks",
]


def _is_placeholder_question(payload):
    options = payload.get("options")
    return (
        payload.get("question", "").startswith(("Generated question ", "Unique question ", "Real ", "Final API ", "Contract question "))
        or options in (["A", "B", "C", "D"], ["Option A", "Option B", "Option C", "Option D"])
    )


def _used_question_ids(attempt):
    ids = set(attempt.answers.values_list("question_id", flat=True))
    if attempt.current_question_id:
        ids.add(attempt.current_question_id)
    return ids


def _is_duplicate_question(question_text, used_question_ids, subject, topic, difficulty):
    normalized = normalize_question_text(question_text)
    return Question.objects.filter(
        id__in=used_question_ids,
        subject=subject,
        topic=topic,
        difficulty=difficulty,
    ).filter(question_text__isnull=False).extra(
        where=["LOWER(REGEXP_REPLACE(TRIM(question_text), E'\\s+', ' ', 'g')) = %s"],
        params=[normalized],
    ).exists()


def _save_generated_question(payload):
    question, _ = Question.objects.get_or_create(
        question_text=payload["question"],
        subject=payload["subject"],
        topic=payload["topic"],
        difficulty=payload["difficulty"],
        defaults={
            "option_a": payload["options"][0],
            "option_b": payload["options"][1],
            "option_c": payload["options"][2],
            "option_d": payload["options"][3],
            "correct_answer": payload["correct_answer"],
            "explanation": payload["explanation"],
        },
    )
    return question


def _materialize_bank_question(subject, topic, item):
    question, _ = Question.objects.get_or_create(
        subject=subject,
        topic=topic,
        question_text=item["question"],
        defaults={
            "difficulty": item["difficulty"],
            "option_a": item["options"]["A"],
            "option_b": item["options"]["B"],
            "option_c": item["options"]["C"],
            "option_d": item["options"]["D"],
            "correct_answer": item["options"][item["correct_answer"]],
            "explanation": item["explanation"],
        },
    )
    return question


def _bank_payload(item):
    return {
        "id": item["id"],
        "question": item["question"],
        "options": [item["options"][key] for key in ("A", "B", "C", "D")],
        "correct_answer": item["options"][item["correct_answer"]],
        "explanation": item["explanation"],
        "subject": item.get("subject"),
        "topic": item.get("topic"),
        "difficulty": item["difficulty"],
    }


def home(request):
    return render(request, "home.html")


@login_required
def technical_languages(request):
    query = request.GET.get("q", "").strip()
    results = []
    if query:
        query_lower = query.lower()
        results = [
            item for item in all_search_items()
            if query_lower in item["title"].lower() or query_lower in item["description"].lower() or query_lower in item.get("matching_section", "").lower()
        ]
    return render(request, "technical_languages.html", {
        "languages": LANGUAGE_DEFINITIONS,
        "query": query,
        "results": results,
    })


@login_required
def language_topics(request, language_slug):
    language = LANGUAGES.get(language_slug)
    if language is None:
        return redirect("technical_languages")
    completed = request.session.get("notes_completed", [])
    completed_keys = set(completed)
    topic_rows = [
        {"title": topic, "completed": f"{language_slug}:{topic}" in completed_keys}
        for topic in language["topics"]
    ]
    return render(request, "language_topics.html", {
        "language": language,
        "topic_rows": topic_rows,
        "completed_count": sum(row["completed"] for row in topic_rows),
    })


@login_required
def topic_notes(request, language_slug, topic_index):
    language = LANGUAGES.get(language_slug)
    if language is None or topic_index < 0 or topic_index >= len(language["topics"]):
        return redirect("technical_languages")
    topic = language["topics"][topic_index]
    if request.method == "POST":
        completed_key = f"{language_slug}:{topic}"
        completed = set(request.session.get("notes_completed", []))
        if request.POST.get("action") == "toggle_complete":
            if completed_key in completed:
                completed.remove(completed_key)
            else:
                completed.add(completed_key)
            request.session["notes_completed"] = sorted(completed)
        return redirect("topic_notes", language_slug=language_slug, topic_index=topic_index)

    completed = set(request.session.get("notes_completed", []))
    completed_count = sum(
        f"{language_slug}:{item}" in completed for item in language["topics"]
    )
    previous_index = topic_index - 1 if topic_index > 0 else None
    next_index = topic_index + 1 if topic_index < len(language["topics"]) - 1 else None
    return render(request, "topic_notes.html", {
        "language": language,
        "topic": topic,
        "note": language["notes"][topic],
        "topic_index": topic_index,
        "topic_count": len(language["topics"]),
        "completed": f"{language_slug}:{topic}" in completed,
        "completed_count": completed_count,
        "previous_index": previous_index,
        "next_index": next_index,
        "quiz_supported": language["name"] in SUPPORTED_SUBJECTS,
    })


@login_required
def practice_topic(request, language_slug, topic_index):
    language = LANGUAGES.get(language_slug)
    if language is None or topic_index < 0 or topic_index >= len(language["topics"]):
        return redirect("technical_languages")
    topic = language["topics"][topic_index]
    quiz_topics = get_topics_for_subject(language["name"])
    quiz_topic = next(
        (candidate for candidate in quiz_topics if candidate.lower() == topic.lower() or candidate.lower().rstrip("s") == topic.lower().rstrip("s")),
        None,
    )
    if language["name"] not in SUPPORTED_SUBJECTS or quiz_topic is None:
        messages.info(request, "This topic is available for study notes. Choose a supported quiz topic to practise in AdaptiveQuiz.")
        return redirect("select_quiz")
    return redirect(f"{reverse('select_quiz')}?subject={language['name']}&topic={quiz_topic}")


def register_view(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful. Welcome to AdaptiveQuiz!")
            return redirect("dashboard")
    else:
        form = RegistrationForm()
    return render(request, "register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("dashboard")
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
    return render(request, "login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    return redirect("home")


@login_required
def dashboard(request):
    user = request.user
    attempts = QuizAttempt.objects.filter(user=user)
    total_quizzes = attempts.count()
    total_questions = AnswerRecord.objects.filter(user=user).count()
    correct_answers = AnswerRecord.objects.filter(user=user, is_correct=True).count()
    accuracy = calculate_accuracy(correct_answers, total_questions) if total_questions else 0
    recent_attempts = attempts[:5]

    topic_performance = TopicPerformance.objects.filter(user=user)
    strongest_topic = topic_performance.order_by("-accuracy").first()
    weakest_topic = topic_performance.order_by("accuracy").first()

    overall_skill = get_skill_level(accuracy)
    chart_data = []
    for item in topic_performance:
        chart_data.append({"label": f"{item.subject} - {item.topic}", "value": float(item.accuracy)})

    context = {
        "total_quizzes": total_quizzes,
        "total_questions": total_questions,
        "accuracy": accuracy,
        "skill_level": overall_skill,
        "strongest_topic": strongest_topic,
        "weakest_topic": weakest_topic,
        "recent_attempts": recent_attempts,
        "chart_data": chart_data,
        "subjects": SUPPORTED_SUBJECTS,
    }
    return render(request, "dashboard.html", context)


@login_required
def select_quiz(request):
    if request.method == "POST":
        form = QuizSelectionForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data["subject"]
            topic = form.cleaned_data["topic"]
            try:
                selected_question_ids = select_question_ids(subject, topic, get_default_quiz_length())
            except (QuestionBankError, KeyError):
                messages.error(request, "This topic does not have a valid 13-question bank yet.")
                return redirect("select_quiz")
            request.session["quiz_subject"] = subject
            request.session["quiz_topic"] = topic
            request.session["current_difficulty"] = "Easy"
            request.session["quiz_length"] = getattr(settings, "QUIZ_SETTINGS", {}).get("DEFAULT_QUIZ_LENGTH", get_default_quiz_length())
            request.session["question_index"] = 0
            request.session["quiz_results"] = []
            request.session["generated_questions"] = []
            request.session["prefetched_questions"] = {}
            request.session["current_question_data"] = None
            attempt = QuizAttempt.objects.create(
                user=request.user,
                subject=subject,
                topic=topic,
                total_questions=0,
                score=0,
                current_question_number=1,
                current_difficulty="Easy",
                highest_difficulty="Easy",
                status="in_progress",
                selected_question_ids=selected_question_ids,
            )
            request.session["quiz_attempt_id"] = attempt.id
            return redirect("quiz_page")
    else:
        form = QuizSelectionForm(initial={
            "subject": request.GET.get("subject", ""),
            "topic": request.GET.get("topic", ""),
        })

    context = {
        "form": form,
        "subjects": SUPPORTED_SUBJECTS,
        "topics_by_subject": {subject: get_topics_for_subject(subject) for subject in SUPPORTED_SUBJECTS},
    }
    return render(request, "select_quiz.html", context)


@login_required
def quiz_page(request):
    subject = request.session.get("quiz_subject")
    topic = request.session.get("quiz_topic")
    if not subject or not topic:
        return redirect("select_quiz")

    if request.method == "POST":
        if request.POST.get("action") == "next":
            request.session["question_index"] = int(request.session.get("question_index", 0)) + 1
            return redirect("quiz_page")

    question_index = int(request.session.get("question_index", 0))
    quiz_length = int(request.session.get("quiz_length", get_default_quiz_length()))
    current_difficulty = request.session.get("current_difficulty", "Easy")
    attempt = QuizAttempt.objects.filter(
        id=request.session.get("quiz_attempt_id"),
        user=request.user,
        status="in_progress",
    ).first()
    if attempt is None:
        return redirect("select_quiz")

    if question_index >= quiz_length:
        return redirect("quiz_result")

    question_id = attempt.selected_question_ids[question_index]
    try:
        item = get_bank_question(subject, topic, question_id)
        if item is None:
            raise QuestionBankError("Selected question is missing from the question bank.")
    except (QuestionBankError, KeyError, IndexError):
        messages.error(request, "The question bank is invalid for this quiz topic.")
        return redirect("select_quiz")

    question_payload = _bank_payload(item)
    question_payload["subject"] = subject
    question_payload["topic"] = topic
    current_difficulty = item["difficulty"]
    question = _materialize_bank_question(subject, topic, item)
    request.session["current_question_id"] = question.id
    request.session["current_question_data"] = question_payload
    attempt.current_question = question
    attempt.current_question_number = question_index + 1
    attempt.current_difficulty = current_difficulty
    attempt.save(update_fields=["current_question", "current_question_number", "current_difficulty"])
    return render(
        request,
        "quiz.html",
        {
            "question_number": question_index + 1,
            "total_questions": quiz_length,
            "subject": subject,
            "topic": topic,
            "difficulty": current_difficulty,
            "question": question_payload,
            "progress": ((question_index + 1) / quiz_length) * 100,
        },
    )


@login_required
def prefetch_question(request):
    if request.method != "GET":
        return JsonResponse({"success": False}, status=405)
    return JsonResponse({"success": True, "cached": True})


@login_required
def submit_answer(request):
    if request.method != "POST":
        return redirect("select_quiz")

    question_data = request.session.get("current_question_data")
    if not question_data:
        return redirect("select_quiz")

    selected_answer = request.POST.get("selected_answer")
    if not selected_answer:
        messages.error(request, "Please select an answer.")
        return redirect("quiz_page")

    question = Question.objects.filter(
        question_text=question_data["question"],
        subject=question_data["subject"],
        topic=question_data["topic"],
        difficulty=question_data["difficulty"],
    ).order_by("-created_at").first()

    if question is None:
        question = Question.objects.create(
            subject=question_data["subject"],
            topic=question_data["topic"],
            difficulty=question_data["difficulty"],
            question_text=question_data["question"],
            option_a=question_data["options"][0],
            option_b=question_data["options"][1],
            option_c=question_data["options"][2],
            option_d=question_data["options"][3],
            correct_answer=question_data["correct_answer"],
            explanation=question_data["explanation"],
        )

    is_correct = selected_answer == question.correct_answer
    quiz_attempt = QuizAttempt.objects.filter(
        id=request.session.get("quiz_attempt_id"),
        user=request.user,
        status="in_progress",
    ).first()
    if quiz_attempt is None:
        return redirect("select_quiz")
    if AnswerRecord.objects.filter(quiz_attempt=quiz_attempt, question=question).exists():
        messages.error(request, "This question has already been answered.")
        return redirect("quiz_page")

    try:
        with transaction.atomic():
            AnswerRecord.objects.create(
                user=request.user,
                quiz_attempt=quiz_attempt,
                question=question,
                selected_answer=selected_answer,
                correct_answer=question.correct_answer,
                is_correct=is_correct,
                time_taken=int(request.POST.get("time_taken", 0) or 0),
            )
    except IntegrityError:
        messages.error(request, "This question has already been answered.")
        return redirect("quiz_page")

    topic_performance, created = TopicPerformance.objects.get_or_create(
        user=request.user,
        subject=request.session.get("quiz_subject"),
        topic=request.session.get("quiz_topic"),
    )
    topic_performance.total_questions += 1
    if is_correct:
        topic_performance.correct_answers += 1
    topic_performance.accuracy = calculate_accuracy(topic_performance.correct_answers, topic_performance.total_questions)
    topic_performance.current_level = "Strong" if topic_performance.accuracy >= 75 else "Weak" if topic_performance.accuracy < 50 else "Average"
    topic_performance.save()

    recent_results = request.session.get("quiz_results", [])
    recent_results.append(is_correct)
    if len(recent_results) > 10:
        recent_results = recent_results[-10:]
    request.session["quiz_results"] = recent_results

    from .adaptive_engine import get_next_difficulty

    current_difficulty = question_data["difficulty"]
    next_difficulty = get_next_difficulty(current_difficulty, recent_results)
    request.session["current_difficulty"] = next_difficulty

    quiz_attempt.total_questions += 1
    if is_correct:
        quiz_attempt.score += 1
    quiz_attempt.accuracy = calculate_accuracy(quiz_attempt.score, quiz_attempt.total_questions)
    quiz_attempt.highest_difficulty = max([quiz_attempt.highest_difficulty, next_difficulty], key=lambda val: ["Easy", "Medium", "Hard"].index(val))
    quiz_attempt.save()

    next_index = int(request.session.get("question_index", 0)) + 1

    if next_index >= int(request.session.get("quiz_length", 10)):
        quiz_attempt.status = "completed"
        quiz_attempt.save(update_fields=["status"])
        request.session["question_index"] = next_index
        return redirect("quiz_result")

    return render(
        request,
        "quiz.html",
        {
            "question_number": int(request.session.get("question_index", 0)) + 1,
            "total_questions": request.session.get("quiz_length", 10),
            "subject": request.session.get("quiz_subject"),
            "topic": request.session.get("quiz_topic"),
            "difficulty": question_data["difficulty"],
            "question": question_data,
            "progress": ((int(request.session.get("question_index", 0)) + 1) / int(request.session.get("quiz_length", 10))) * 100,
            "result": {
                "correct": is_correct,
                "explanation": question.explanation,
                "next_difficulty": next_difficulty,
                "was_submitted": True,
            },
        },
    )


@login_required
def quiz_result(request):
    user = request.user
    attempts = QuizAttempt.objects.filter(user=user).order_by("-completed_at")
    latest_attempt = attempts.first()
    if latest_attempt is None:
        return render(request, "result.html", {"result": None})

    total_questions = latest_attempt.total_questions or 0
    correct_answers = latest_attempt.score or 0
    wrong_answers = max(total_questions - correct_answers, 0)
    accuracy = latest_attempt.accuracy or 0
    strong_topics = TopicPerformance.objects.filter(user=user, accuracy__gte=75).order_by("-accuracy")[:3]
    weak_topics = TopicPerformance.objects.filter(user=user, accuracy__lt=50).order_by("accuracy")[:3]

    context = {
        "score": latest_attempt.score,
        "total_questions": total_questions,
        "correct_answers": correct_answers,
        "wrong_answers": wrong_answers,
        "accuracy": accuracy,
        "highest_difficulty": latest_attempt.highest_difficulty,
        "strong_topics": strong_topics,
        "weak_topics": weak_topics,
    }
    return render(request, "result.html", context)


@login_required
def quiz_history(request):
    attempts = list(QuizAttempt.objects.filter(user=request.user).order_by("-completed_at", "-id"))
    accuracies = [float(attempt.accuracy) for attempt in attempts]
    best_attempt = max(attempts, key=lambda attempt: float(attempt.accuracy), default=None)
    return render(request, "history.html", {
        "attempts": attempts,
        "history_stats": {
            "total": len(attempts),
            "average_accuracy": round(sum(accuracies) / len(accuracies)) if accuracies else 0,
            "best_accuracy": round(float(best_attempt.accuracy)) if best_attempt else 0,
        },
        "best_attempt": best_attempt,
    })


@login_required
def performance(request):
    topic_data = TopicPerformance.objects.filter(user=request.user)
    return render(request, "performance.html", {"topics": topic_data})


def api_generate_question(request):
    if not request.user.is_authenticated:
        return render(request, "login.html", {})

    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Only POST requests are allowed."}, status=405)

    data = json.loads(request.body or "{}")
    subject = (data.get("subject") or "").strip()
    topic = (data.get("topic") or "").strip()
    difficulty = (data.get("difficulty") or "Easy").strip()

    if subject not in SUPPORTED_SUBJECTS:
        return JsonResponse({"success": False, "message": "Invalid subject."}, status=400)
    if not topic:
        return JsonResponse({"success": False, "message": "Topic is required."}, status=400)
    if difficulty not in {"Easy", "Medium", "Hard"}:
        return JsonResponse({"success": False, "message": "Invalid difficulty."}, status=400)

    generated = generate_question(subject, topic, difficulty)
    if not generated.get("success"):
        return JsonResponse({"success": False, "message": generated.get("message", "Question generation failed.")}, status=400)

    question_data = generated["question"]
    question = Question.objects.create(
        subject=question_data["subject"],
        topic=question_data["topic"],
        difficulty=question_data["difficulty"],
        question_text=question_data["question"],
        option_a=question_data["options"][0],
        option_b=question_data["options"][1],
        option_c=question_data["options"][2],
        option_d=question_data["options"][3],
        correct_answer=question_data["correct_answer"],
        explanation=question_data["explanation"],
    )

    return JsonResponse({
        "success": True,
        "question": {
            "id": question.id,
            "question": question.question_text,
            "options": question.options(),
            "difficulty": question.difficulty,
            "topic": question.topic,
        },
    })


def api_submit_answer(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "Authentication required."}, status=401)

    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Only POST requests are allowed."}, status=405)

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON payload."}, status=400)

    question_id = payload.get("question_id")
    selected_answer = payload.get("selected_answer")
    time_taken = payload.get("time_taken", 0)

    if not question_id:
        return JsonResponse({"success": False, "message": "Question ID is required."}, status=400)

    try:
        question = Question.objects.get(id=question_id)
    except Question.DoesNotExist:
        return JsonResponse({"success": False, "message": "Question not found."}, status=404)

    if selected_answer not in question.options():
        return JsonResponse({"success": False, "message": "Invalid answer."}, status=400)

    is_correct = selected_answer == question.correct_answer
    attempt = QuizAttempt.objects.filter(user=request.user).order_by("-completed_at").first()
    if attempt is None:
        attempt = QuizAttempt.objects.create(user=request.user, subject=question.subject, topic=question.topic, total_questions=0, score=0)

    AnswerRecord.objects.create(
        user=request.user,
        quiz_attempt=attempt,
        question=question,
        selected_answer=selected_answer,
        correct_answer=question.correct_answer,
        is_correct=is_correct,
        time_taken=time_taken,
    )

    tp, _ = TopicPerformance.objects.get_or_create(user=request.user, subject=question.subject, topic=question.topic)
    tp.total_questions += 1
    if is_correct:
        tp.correct_answers += 1
    tp.accuracy = calculate_accuracy(tp.correct_answers, tp.total_questions)
    tp.current_level = "Strong" if tp.accuracy >= 75 else "Weak" if tp.accuracy < 50 else "Average"
    tp.save()

    attempt.total_questions += 1
    if is_correct:
        attempt.score += 1
    attempt.accuracy = calculate_accuracy(attempt.score, attempt.total_questions)
    attempt.subject = question.subject
    attempt.topic = question.topic
    attempt.save()

    next_difficulty = "Easy"
    return JsonResponse({"correct": is_correct, "explanation": question.explanation, "next_difficulty": next_difficulty})


def api_dashboard(request):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required."}, status=401)

    attempts = QuizAttempt.objects.filter(user=request.user)
    total_questions = AnswerRecord.objects.filter(user=request.user).count()
    correct_answers = AnswerRecord.objects.filter(user=request.user, is_correct=True).count()
    data = {
        "total_quizzes": attempts.count(),
        "total_questions": total_questions,
        "overall_accuracy": calculate_accuracy(correct_answers, total_questions),
        "skill_level": get_skill_level(calculate_accuracy(correct_answers, total_questions)),
    }
    return JsonResponse(data)


def api_performance(request):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required."}, status=401)

    rows = TopicPerformance.objects.filter(user=request.user)
    return JsonResponse({
        "topics": [
            {
                "subject": row.subject,
                "topic": row.topic,
                "total_questions": row.total_questions,
                "correct_answers": row.correct_answers,
                "accuracy": row.accuracy,
                "current_level": row.current_level,
            }
            for row in rows
        ]
    })


def api_quiz_history(request):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required."}, status=401)

    attempts = QuizAttempt.objects.filter(user=request.user)
    return JsonResponse({
        "history": [
            {
                "id": item.id,
                "subject": item.subject,
                "topic": item.topic,
                "score": item.score,
                "accuracy": item.accuracy,
                "highest_difficulty": item.highest_difficulty,
                "completed_at": item.completed_at.isoformat(),
            }
            for item in attempts
        ]
    })


def api_topics(request):
    return JsonResponse({"topics": {subject: get_topics_for_subject(subject) for subject in SUPPORTED_SUBJECTS}})
