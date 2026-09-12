from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("quiz", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="quizattempt",
            name="current_difficulty",
            field=models.CharField(default="Easy", max_length=20),
        ),
        migrations.AddField(
            model_name="quizattempt",
            name="current_question",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="active_attempts", to="quiz.question"),
        ),
        migrations.AddField(
            model_name="quizattempt",
            name="current_question_number",
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name="quizattempt",
            name="status",
            field=models.CharField(choices=[("in_progress", "In progress"), ("completed", "Completed")], default="in_progress", max_length=20),
        ),
    ]
