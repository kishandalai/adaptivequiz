from django.conf import settings
from django.db import models


class SubjectTopic(models.Model):
    subject = models.CharField(max_length=100)
    topic = models.CharField(max_length=100)

    class Meta:
        unique_together = ("subject", "topic")

    def __str__(self):
        return f"{self.subject} - {self.topic}"


class TechnicalNote(models.Model):
    language_slug = models.SlugField(max_length=100)
    language_name = models.CharField(max_length=100)
    topic = models.CharField(max_length=150)
    content = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["language_name", "topic"]
        constraints = [
            models.UniqueConstraint(
                fields=["language_slug", "topic"],
                name="unique_technical_note_topic",
            ),
        ]

    def __str__(self):
        return f"{self.language_name} - {self.topic}"


class Question(models.Model):
    DIFFICULTY_CHOICES = [
        ("Easy", "Easy"),
        ("Medium", "Medium"),
        ("Hard", "Hard"),
    ]

    subject = models.CharField(max_length=100)
    topic = models.CharField(max_length=100)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default="Easy")
    question_text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_answer = models.CharField(max_length=255)
    explanation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def options(self):
        return [self.option_a, self.option_b, self.option_c, self.option_d]

    def __str__(self):
        return f"{self.subject} - {self.topic} - {self.difficulty}"


class QuizAttempt(models.Model):
    STATUS_CHOICES = [
        ("in_progress", "In progress"),
        ("completed", "Completed"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_attempts")
    subject = models.CharField(max_length=100)
    topic = models.CharField(max_length=100)
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    accuracy = models.FloatField(default=0.0)
    highest_difficulty = models.CharField(max_length=20, default="Easy")
    current_question_number = models.IntegerField(default=1)
    current_difficulty = models.CharField(max_length=20, default="Easy")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="in_progress")
    current_question = models.ForeignKey("Question", null=True, blank=True, on_delete=models.SET_NULL, related_name="active_attempts")
    selected_question_ids = models.JSONField(default=list)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-completed_at"]

    def __str__(self):
        return f"{self.user.username} - {self.subject} - {self.topic}"


class AnswerRecord(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="answer_records")
    quiz_attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answer_records")
    selected_answer = models.CharField(max_length=255)
    correct_answer = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    time_taken = models.IntegerField(default=0)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-answered_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["quiz_attempt", "question"],
                name="unique_question_per_quiz_attempt",
            ),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.question.subject} - {self.is_correct}"


class TopicPerformance(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="topic_performance")
    subject = models.CharField(max_length=100)
    topic = models.CharField(max_length=100)
    total_questions = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    accuracy = models.FloatField(default=0.0)
    current_level = models.CharField(max_length=20, default="Average")

    class Meta:
        unique_together = ("user", "subject", "topic")
        ordering = ["-accuracy", "topic"]

    def __str__(self):
        return f"{self.user.username} - {self.subject} - {self.topic}"
