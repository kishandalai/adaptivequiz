from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("quiz", "0002_quizattempt_lifecycle"),
    ]

    operations = [
        migrations.RunPython(
            code=lambda apps, schema_editor: _remove_duplicate_answers(apps),
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AddConstraint(
            model_name="answerrecord",
            constraint=models.UniqueConstraint(
                fields=("quiz_attempt", "question"),
                name="unique_question_per_quiz_attempt",
            ),
        ),
    ]


def _remove_duplicate_answers(apps):
    AnswerRecord = apps.get_model("quiz", "AnswerRecord")
    seen = set()
    duplicate_ids = []
    for record in AnswerRecord.objects.order_by("id").iterator():
        key = (record.quiz_attempt_id, record.question_id)
        if key in seen:
            duplicate_ids.append(record.id)
        else:
            seen.add(key)
    if duplicate_ids:
        AnswerRecord.objects.filter(id__in=duplicate_ids).delete()
