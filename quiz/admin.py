from django.contrib import admin

from .models import AnswerRecord, Question, QuizAttempt, TechnicalNote, TopicPerformance


@admin.register(TechnicalNote)
class TechnicalNoteAdmin(admin.ModelAdmin):
    list_display = ("language_name", "topic", "updated_at")
    search_fields = ("language_name", "topic")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "topic", "difficulty", "question_text", "created_at")
    search_fields = ("subject", "topic", "question_text")
    list_filter = ("subject", "topic", "difficulty")


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "subject", "topic", "score", "total_questions", "accuracy", "highest_difficulty", "completed_at")
    search_fields = ("user__username", "subject", "topic")
    list_filter = ("subject", "topic", "highest_difficulty")


@admin.register(AnswerRecord)
class AnswerRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "question", "selected_answer", "correct_answer", "is_correct", "answered_at")
    search_fields = ("user__username", "question__question_text")
    list_filter = ("is_correct",)


@admin.register(TopicPerformance)
class TopicPerformanceAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "subject", "topic", "total_questions", "correct_answers", "accuracy", "current_level")
    search_fields = ("user__username", "subject", "topic")
    list_filter = ("subject", "current_level")
