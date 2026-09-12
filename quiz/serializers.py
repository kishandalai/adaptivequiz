from rest_framework import serializers

from .models import AnswerRecord, Question, QuizAttempt, TopicPerformance


class QuestionSerializer(serializers.ModelSerializer):
    question = serializers.SerializerMethodField()
    options = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ["id", "question", "options", "difficulty", "topic", "subject"]

    def get_question(self, obj):
        return obj.question_text

    def get_options(self, obj):
        return obj.options()


class SubmitAnswerSerializer(serializers.Serializer):
    question_id = serializers.CharField()
    selected_option = serializers.ChoiceField(choices=["A", "B", "C", "D"])
    time_taken = serializers.IntegerField(min_value=0)


class GenerateQuestionRequestSerializer(serializers.Serializer):
    subject = serializers.CharField()
    topic = serializers.CharField()
    difficulty = serializers.ChoiceField(choices=["Easy", "Medium", "Hard"])


class StartQuizRequestSerializer(serializers.Serializer):
    subject = serializers.CharField()
    topic = serializers.CharField()


class NextQuestionRequestSerializer(serializers.Serializer):
    previous_question_id = serializers.CharField()


class QuestionResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    subject = serializers.CharField()
    topic = serializers.CharField()
    difficulty = serializers.CharField()
    question = serializers.CharField()
    options = serializers.ListField(child=serializers.DictField())


class QuizResultResponseSerializer(serializers.Serializer):
    quiz_id = serializers.IntegerField()
    subject = serializers.CharField()
    topic = serializers.CharField()
    total_questions = serializers.IntegerField()
    correct_answers = serializers.IntegerField()
    wrong_answers = serializers.IntegerField()
    score = serializers.IntegerField()
    accuracy = serializers.FloatField()
    highest_difficulty = serializers.CharField()
    status = serializers.CharField()


class DashboardResponseSerializer(serializers.Serializer):
    username = serializers.CharField()
    total_quizzes = serializers.IntegerField()
    total_questions = serializers.IntegerField()
    total_correct = serializers.IntegerField()
    overall_accuracy = serializers.FloatField()
    current_level = serializers.CharField()
    strongest_topic = serializers.CharField(allow_null=True)
    weakest_topic = serializers.CharField(allow_null=True)


class PerformanceResponseSerializer(serializers.Serializer):
    overall = serializers.DictField()
    topics = serializers.ListField(child=serializers.DictField())


class QuizHistoryResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    subject = serializers.CharField()
    topic = serializers.CharField()
    score = serializers.IntegerField()
    total_questions = serializers.IntegerField()
    accuracy = serializers.FloatField()
    highest_difficulty = serializers.CharField()
    status = serializers.CharField()
    completed_at = serializers.DateTimeField()


class TopicPerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TopicPerformance
        fields = ["id", "subject", "topic", "total_questions", "correct_answers", "accuracy", "current_level"]


class QuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = ["id", "subject", "topic", "score", "total_questions", "accuracy", "highest_difficulty", "started_at", "completed_at"]


class AnswerRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerRecord
        fields = ["id", "question", "selected_answer", "correct_answer", "is_correct", "time_taken", "answered_at"]
