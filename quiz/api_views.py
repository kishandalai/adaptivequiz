from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import APIException, NotAuthenticated
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .adaptive_engine import calculate_accuracy, get_next_difficulty, get_skill_level
from .gemini_service import generate_question
from .models import AnswerRecord, Question, QuizAttempt, TopicPerformance
from .question_bank import QuestionBankError, get_bank_question, load_question_bank, public_question, select_question_ids
from .views import _materialize_bank_question
from .serializers import (
    GenerateQuestionRequestSerializer,
    NextQuestionRequestSerializer,
    StartQuizRequestSerializer,
    SubmitAnswerSerializer,
)
from .utils import get_topics_for_subject, normalize_question_text
from .views import SUPPORTED_SUBJECTS, _is_placeholder_question

DIFFICULTIES = {"Easy", "Medium", "Hard"}
OPTION_IDS = ("A", "B", "C", "D")
QUIZ_LENGTH = 10


def success(data, status=200):
    return Response({"success": True, **data}, status=status)


def error(code, message, status):
    return Response({"success": False, "error": {"code": code, "message": message}}, status=status)


def question_response(question, number=None):
    if isinstance(question, dict):
        data = public_question(question)
        if number is not None:
            data["question_number"] = number
            data["total_questions"] = QUIZ_LENGTH
        return data
    data = {
        "id": question.id,
        "subject": question.subject,
        "topic": question.topic,
        "difficulty": question.difficulty,
        "question": question.question_text,
        "options": [
            {"id": option_id, "text": text}
            for option_id, text in zip(OPTION_IDS, question.options())
        ],
    }
    if number is not None:
        data["question_number"] = number
        data["total_questions"] = QUIZ_LENGTH
    return data


def quiz_response(attempt):
    return {
        "id": attempt.id,
        "subject": attempt.subject,
        "topic": attempt.topic,
        "total_questions": QUIZ_LENGTH,
        "current_question_number": attempt.current_question_number,
        "current_difficulty": attempt.current_difficulty,
        "status": attempt.status,
    }


def bank_question_for_attempt(attempt, number=None):
    number = number or attempt.current_question_number
    question_id = attempt.selected_question_ids[number - 1]
    item = get_bank_question(attempt.subject, attempt.topic, question_id)
    if item is None:
        raise QuestionBankError("Selected question is missing from the question bank.")
    return item


def api_question(subject, topic, difficulty, excluded_ids=None):
    excluded_ids = excluded_ids or []
    used_texts = {
        normalize_question_text(text)
        for text in Question.objects.filter(id__in=excluded_ids).values_list("question_text", flat=True)
    }
    question = Question.objects.filter(
        subject=subject,
        topic=topic,
        difficulty=difficulty,
    ).exclude(id__in=excluded_ids).exclude(
        option_a="A", option_b="B", option_c="C", option_d="D",
    ).exclude(
        option_a="Option A", option_b="Option B", option_c="Option C", option_d="Option D",
    ).exclude(
        question_text__startswith="Generated question ",
    ).exclude(
        question_text__startswith="Unique question ",
    ).exclude(
        question_text__startswith="Real ",
    ).exclude(
        question_text__startswith="Final API ",
    ).exclude(
        question_text__startswith="Contract question ",
    ).first()
    while question and normalize_question_text(question.question_text) in used_texts:
        excluded_ids.append(question.id)
        question = Question.objects.filter(
            subject=subject,
            topic=topic,
            difficulty=difficulty,
        ).exclude(id__in=excluded_ids).exclude(
            option_a="A", option_b="B", option_c="C", option_d="D",
        ).exclude(
            option_a="Option A", option_b="Option B", option_c="Option C", option_d="Option D",
        ).exclude(
            question_text__startswith="Generated question ",
        ).exclude(
            question_text__startswith="Unique question ",
        ).exclude(
            question_text__startswith="Real ",
        ).exclude(
            question_text__startswith="Final API ",
        ).exclude(
            question_text__startswith="Contract question ",
        ).first()
    if question:
        return question

    excluded_texts = list(
        Question.objects.filter(id__in=excluded_ids).values_list("question_text", flat=True)
    )
    payload = None
    for _ in range(3):
        generated = generate_question(subject, topic, difficulty, excluded_texts)
        if not generated.get("success"):
            return None
        candidate = generated["question"]
        if not _is_placeholder_question(candidate) and normalize_question_text(candidate["question"]) not in used_texts:
            payload = candidate
            break
    if payload is None:
        return None
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


def current_attempt_for_question(user, question_id):
    return QuizAttempt.objects.filter(
        user=user,
        status="in_progress",
        current_question_id=question_id,
    ).first()


def attempt_results(attempt):
    return list(attempt.answers.order_by("answered_at").values_list("is_correct", flat=True))[-10:]


def update_topic_performance(user, question, is_correct):
    performance, _ = TopicPerformance.objects.get_or_create(
        user=user,
        subject=question.subject,
        topic=question.topic,
    )
    performance.total_questions += 1
    if is_correct:
        performance.correct_answers += 1
    performance.accuracy = calculate_accuracy(performance.correct_answers, performance.total_questions)
    performance.current_level = "Strong" if performance.accuracy >= 75 else "Weak" if performance.accuracy < 50 else "Average"
    performance.save()


class ContractAPIView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def handle_exception(self, exc):
        if isinstance(exc, NotAuthenticated):
            return error("UNAUTHORIZED", "Authentication is required.", 401)
        if isinstance(exc, APIException):
            return error("INVALID_REQUEST", str(exc.detail), exc.status_code)
        return error("INTERNAL_ERROR", "An unexpected server error occurred.", 500)


class GenerateQuestionAPI(ContractAPIView):
    def post(self, request):
        serializer = GenerateQuestionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            code = "INVALID_DIFFICULTY" if "difficulty" in serializer.errors else "INVALID_REQUEST"
            message = "Difficulty must be Easy, Medium, or Hard." if code == "INVALID_DIFFICULTY" else next(iter(serializer.errors.values()))[0]
            return error(code, message, 400)
        data = serializer.validated_data
        if data["subject"] not in SUPPORTED_SUBJECTS:
            return error("INVALID_REQUEST", "Subject is not supported.", 400)
        question = api_question(data["subject"], data["topic"], data["difficulty"])
        if not question:
            return error("GEMINI_ERROR", "Unable to generate a question right now. Please try again.", 502)
        return success({"question": question_response(question)})


class SubmitAnswerAPI(ContractAPIView):
    def post(self, request):
        serializer = SubmitAnswerSerializer(data=request.data)
        if not serializer.is_valid():
            code = "INVALID_ANSWER" if "selected_option" in serializer.errors else "INVALID_REQUEST"
            message = "Please select a valid answer." if code == "INVALID_ANSWER" else next(iter(serializer.errors.values()))[0]
            return error(code, message, 400)
        data = serializer.validated_data
        attempt = None
        question = None
        for candidate_attempt in QuizAttempt.objects.filter(user=request.user, status="in_progress"):
            if candidate_attempt.current_question_number > len(candidate_attempt.selected_question_ids):
                continue
            try:
                current_item = bank_question_for_attempt(candidate_attempt)
            except (QuestionBankError, IndexError):
                continue
            if current_item["id"] == data["question_id"]:
                attempt = candidate_attempt
                question = _materialize_bank_question(candidate_attempt.subject, candidate_attempt.topic, current_item)
                break
        if question is None and str(data["question_id"]).isdigit():
            try:
                question = Question.objects.get(id=int(data["question_id"]))
            except Question.DoesNotExist:
                question = None
        if question is None:
            return error("QUESTION_NOT_FOUND", "The requested question was not found.", 404)

        if attempt is None:
            attempt = current_attempt_for_question(request.user, question.id)
        if attempt is None:
            completed = QuizAttempt.objects.filter(user=request.user, current_question_id=question.id, status="completed").exists()
            if completed:
                return error("QUIZ_COMPLETED", "This quiz has already been completed.", 409)
            return error("QUESTION_NOT_FOUND", "The requested question was not found in an active quiz.", 404)
        if AnswerRecord.objects.filter(quiz_attempt=attempt, question=question).exists():
            return error("ANSWER_ALREADY_SUBMITTED", "This question has already been answered.", 409)

        selected_text = dict(zip(OPTION_IDS, question.options())).get(data["selected_option"])
        if selected_text is None:
            return error("INVALID_ANSWER", "Please select a valid answer.", 400)
        is_correct = selected_text == question.correct_answer
        results = attempt_results(attempt) + [is_correct]
        current_difficulty = question.difficulty
        next_difficulty = get_next_difficulty(current_difficulty, results)

        with transaction.atomic():
            try:
                AnswerRecord.objects.create(
                    user=request.user,
                    quiz_attempt=attempt,
                    question=question,
                    selected_answer=selected_text,
                    correct_answer=question.correct_answer,
                    is_correct=is_correct,
                    time_taken=data["time_taken"],
                )
            except IntegrityError:
                return error("ANSWER_ALREADY_SUBMITTED", "This question has already been answered.", 409)
            update_topic_performance(request.user, question, is_correct)
            attempt.total_questions = attempt.answers.count()
            attempt.score = attempt.answers.filter(is_correct=True).count()
            attempt.accuracy = calculate_accuracy(attempt.score, attempt.total_questions)
            attempt.current_difficulty = next_difficulty
            attempt.highest_difficulty = max(
                [attempt.highest_difficulty, next_difficulty],
                key=lambda value: ["Easy", "Medium", "Hard"].index(value),
            )
            attempt.save()

        consecutive_correct = 0
        consecutive_wrong = 0
        for result in reversed(results):
            if result:
                if consecutive_wrong:
                    break
                consecutive_correct += 1
            else:
                if consecutive_correct:
                    break
                consecutive_wrong += 1
        return success({"result": {
            "is_correct": is_correct,
            "explanation": question.explanation,
            "correct_option": OPTION_IDS[question.options().index(question.correct_answer)],
            "current_difficulty": current_difficulty,
            "next_difficulty": next_difficulty,
            "consecutive_correct": consecutive_correct,
            "consecutive_wrong": consecutive_wrong,
        }})


class StartQuizAPI(ContractAPIView):
    def post(self, request):
        serializer = StartQuizRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return error("INVALID_REQUEST", next(iter(serializer.errors.values()))[0], 400)
        data = serializer.validated_data
        if data["subject"] not in SUPPORTED_SUBJECTS:
            return error("INVALID_REQUEST", "Subject is not supported.", 400)
        with transaction.atomic():
            try:
                selected_ids = select_question_ids(data["subject"], data["topic"], QUIZ_LENGTH)
                item = get_bank_question(data["subject"], data["topic"], selected_ids[0])
            except (QuestionBankError, KeyError, IndexError):
                transaction.set_rollback(True)
                return error("QUESTION_BANK_INVALID", "This topic does not have a valid 13-question bank.", 500)
            question = _materialize_bank_question(data["subject"], data["topic"], item)
            attempt = QuizAttempt.objects.create(
                user=request.user,
                subject=data["subject"],
                topic=data["topic"],
                total_questions=0,
                score=0,
                current_question_number=1,
                current_difficulty="Easy",
                highest_difficulty="Easy",
                status="in_progress",
                current_question=question,
                selected_question_ids=selected_ids,
            )
        return success({"quiz": quiz_response(attempt)}, 201)


class CurrentQuestionAPI(ContractAPIView):
    def get(self, request, quiz_id):
        try:
            attempt = QuizAttempt.objects.get(id=quiz_id, user=request.user)
        except QuizAttempt.DoesNotExist:
            return error("QUIZ_NOT_FOUND", "The requested quiz was not found.", 404)
        try:
            item = bank_question_for_attempt(attempt)
        except (QuestionBankError, IndexError):
            return error("QUESTION_NOT_FOUND", "The requested question was not found.", 404)
        return success({"question": question_response(item, attempt.current_question_number)})


class NextQuestionAPI(ContractAPIView):
    def post(self, request, quiz_id):
        serializer = NextQuestionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return error("INVALID_REQUEST", next(iter(serializer.errors.values()))[0], 400)
        try:
            attempt = QuizAttempt.objects.get(id=quiz_id, user=request.user)
        except QuizAttempt.DoesNotExist:
            return error("QUIZ_NOT_FOUND", "The requested quiz was not found.", 404)
        if attempt.status == "completed":
            return error("QUIZ_COMPLETED", "This quiz has already been completed.", 409)
        try:
            current_item = bank_question_for_attempt(attempt)
        except (QuestionBankError, IndexError):
            return error("QUESTION_NOT_FOUND", "The requested question was not found.", 404)
        if current_item["id"] != serializer.validated_data["previous_question_id"]:
            return error("QUESTION_NOT_FOUND", "The requested question was not found.", 404)
        if attempt.current_question_number >= QUIZ_LENGTH:
            return error("QUIZ_COMPLETED", "Complete this quiz before requesting another question.", 409)
        if not attempt.answers.filter(question_id=attempt.current_question_id).exists():
            return error("QUESTION_NOT_ANSWERED", "Submit an answer before requesting the next question.", 409)
        try:
            next_item = bank_question_for_attempt(attempt, attempt.current_question_number + 1)
        except (QuestionBankError, IndexError):
            return error("QUESTION_BANK_INVALID", "The selected question bank is invalid.", 500)
        question = _materialize_bank_question(attempt.subject, attempt.topic, next_item)
        attempt.current_question = question
        attempt.current_question_number += 1
        attempt.save(update_fields=["current_question", "current_question_number"])
        return success({"quiz": quiz_response(attempt), "question": question_response(next_item, attempt.current_question_number)})


class CompleteQuizAPI(ContractAPIView):
    def post(self, request, quiz_id):
        try:
            attempt = QuizAttempt.objects.get(id=quiz_id, user=request.user)
        except QuizAttempt.DoesNotExist:
            return error("QUIZ_NOT_FOUND", "The requested quiz was not found.", 404)
        if attempt.status == "completed":
            return error("QUIZ_COMPLETED", "This quiz has already been completed.", 409)
        attempt.status = "completed"
        attempt.completed_at = timezone.now()
        attempt.save(update_fields=["status", "completed_at"])
        return success({"result": {
            "quiz_id": attempt.id,
            "subject": attempt.subject,
            "topic": attempt.topic,
            "total_questions": attempt.total_questions,
            "correct_answers": attempt.score,
            "wrong_answers": max(attempt.total_questions - attempt.score, 0),
            "score": attempt.score,
            "accuracy": attempt.accuracy,
            "highest_difficulty": attempt.highest_difficulty,
            "status": attempt.status,
        }})


class DashboardAPI(ContractAPIView):
    def get(self, request):
        answers = AnswerRecord.objects.filter(user=request.user)
        total = answers.count()
        correct = answers.filter(is_correct=True).count()
        performance = TopicPerformance.objects.filter(user=request.user)
        strongest = performance.order_by("-accuracy").first()
        weakest = performance.order_by("accuracy").first()
        accuracy = calculate_accuracy(correct, total)
        return success({"dashboard": {
            "username": request.user.username,
            "total_quizzes": QuizAttempt.objects.filter(user=request.user).count(),
            "total_questions": total,
            "total_correct": correct,
            "overall_accuracy": accuracy,
            "current_level": get_skill_level(accuracy),
            "strongest_topic": f"{strongest.subject} {strongest.topic}" if strongest else None,
            "weakest_topic": f"{weakest.subject} {weakest.topic}" if weakest else None,
        }})


class PerformanceAPI(ContractAPIView):
    def get(self, request):
        rows = TopicPerformance.objects.filter(user=request.user)
        total = sum(row.total_questions for row in rows)
        correct = sum(row.correct_answers for row in rows)
        return success({"performance": {
            "overall": {
                "total_questions": total,
                "correct_answers": correct,
                "wrong_answers": total - correct,
                "accuracy": calculate_accuracy(correct, total),
            },
            "topics": [{
                "subject": row.subject,
                "topic": row.topic,
                "total_questions": row.total_questions,
                "correct_answers": row.correct_answers,
                "accuracy": row.accuracy,
                "level": row.current_level,
            } for row in rows],
        }})


class QuizHistoryAPI(ContractAPIView):
    def get(self, request):
        return success({"history": [{
            "id": attempt.id,
            "subject": attempt.subject,
            "topic": attempt.topic,
            "score": attempt.score,
            "total_questions": attempt.total_questions,
            "accuracy": attempt.accuracy,
            "highest_difficulty": attempt.highest_difficulty,
            "status": attempt.status,
            "completed_at": attempt.completed_at,
        } for attempt in QuizAttempt.objects.filter(user=request.user)]})


class TopicsAPI(ContractAPIView):
    def get(self, request):
        return success({"subjects": [{"name": subject, "topics": get_topics_for_subject(subject)} for subject in SUPPORTED_SUBJECTS]})
