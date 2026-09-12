from django.urls import path

from . import views
from .api_views import (
    CompleteQuizAPI,
    CurrentQuestionAPI,
    DashboardAPI,
    GenerateQuestionAPI,
    NextQuestionAPI,
    PerformanceAPI,
    QuizHistoryAPI,
    StartQuizAPI,
    SubmitAnswerAPI,
    TopicsAPI,
)

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("select-quiz/", views.select_quiz, name="select_quiz"),
    path("quiz/", views.quiz_page, name="quiz_page"),
    path("quiz/prefetch/", views.prefetch_question, name="prefetch_question"),
    path("submit-answer/", views.submit_answer, name="submit_answer"),
    path("result/", views.quiz_result, name="quiz_result"),
    path("history/", views.quiz_history, name="history"),
    path("performance/", views.performance, name="performance"),
    path("technical-languages/", views.technical_languages, name="technical_languages"),
    path("technical-languages/<slug:language_slug>/", views.language_topics, name="language_topics"),
    path("technical-languages/<slug:language_slug>/topic/<int:topic_index>/", views.topic_notes, name="topic_notes"),
    path("technical-languages/<slug:language_slug>/topic/<int:topic_index>/practice/", views.practice_topic, name="practice_topic"),
    path("api/generate-question/", GenerateQuestionAPI.as_view(), name="contract_generate_question"),
    path("api/submit-answer/", SubmitAnswerAPI.as_view(), name="contract_submit_answer"),
    path("api/quiz/start/", StartQuizAPI.as_view(), name="api_quiz_start"),
    path("api/quiz/<int:quiz_id>/question/", CurrentQuestionAPI.as_view(), name="api_quiz_question"),
    path("api/quiz/<int:quiz_id>/next/", NextQuestionAPI.as_view(), name="api_quiz_next"),
    path("api/quiz/<int:quiz_id>/complete/", CompleteQuizAPI.as_view(), name="api_quiz_complete"),
    path("api/dashboard/", DashboardAPI.as_view(), name="contract_dashboard"),
    path("api/performance/", PerformanceAPI.as_view(), name="contract_performance"),
    path("api/quiz-history/", QuizHistoryAPI.as_view(), name="contract_quiz_history"),
    path("api/topics/", TopicsAPI.as_view(), name="contract_topics"),
]
