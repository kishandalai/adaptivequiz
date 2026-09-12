from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("quiz", "0003_answerrecord_unique_per_attempt"),
    ]

    operations = [
        migrations.AddField(
            model_name="quizattempt",
            name="selected_question_ids",
            field=models.JSONField(default=list),
        ),
    ]
