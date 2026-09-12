from functools import wraps

from django.contrib import messages
from django.contrib.auth import logout
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .admin_content import delete_question, find_question, iter_questions, note_rows, save_question
from .admin_forms import AdminNoteForm, AdminQuestionForm
from .learning_notes import get_languages
from .models import TechnicalNote


def admin_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if not (request.user.is_staff or request.user.is_superuser):
            return HttpResponseForbidden("You do not have permission to access the Admin Panel.")
        return view(request, *args, **kwargs)

    return wrapped


def admin_login(request):
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return redirect("admin_dashboard")
    return redirect("login")


def admin_logout(request):
    logout(request)
    return redirect("login")


@admin_required
def admin_dashboard(request):
    questions = list(iter_questions())
    notes = note_rows()
    languages = get_languages()
    return render(request, "admin/dashboard.html", {
        "total_questions": len(questions),
        "total_notes": len(notes),
        "total_languages": len(languages),
        "total_topics": sum(len(language["topics"]) for language in languages.values()),
    })


@admin_required
def admin_questions(request):
    questions = list(iter_questions())
    filters = {key: request.GET.get(key, "").strip() for key in ("company", "subject", "topic", "difficulty", "year", "q")}
    if filters["q"]:
        needle = filters["q"].lower()
        questions = [item for item in questions if needle in item["question"].lower() or needle in item["id"].lower()]
    for key in ("company", "subject", "topic", "difficulty", "year"):
        if filters[key]:
            questions = [item for item in questions if str(item.get(key, "")) == filters[key]]
    return render(request, "admin/questions.html", {"questions": questions, "filters": filters})


@admin_required
def admin_question_create(request):
    form = AdminQuestionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        save_question(form.as_question_data() | {"subject": form.cleaned_data["subject"], "topic": form.cleaned_data["topic"]})
        messages.success(request, "Question added successfully.")
        return redirect("admin_questions")
    return render(request, "admin/question_form.html", {"form": form, "heading": "Add Question"})


@admin_required
def admin_question_edit(request, question_id):
    question = find_question(question_id)
    if question is None:
        raise PermissionDenied("Question not found.")
    initial = {
        **question,
        "option_a": question["options"]["A"],
        "option_b": question["options"]["B"],
        "option_c": question["options"]["C"],
        "option_d": question["options"]["D"],
    }
    form = AdminQuestionForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        data = form.as_question_data() | {"subject": form.cleaned_data["subject"], "topic": form.cleaned_data["topic"]}
        save_question(data, question_id=question_id)
        messages.success(request, "Question updated successfully.")
        return redirect("admin_questions")
    return render(request, "admin/question_form.html", {"form": form, "heading": "Edit Question"})


@admin_required
def admin_question_delete(request, question_id):
    if request.method == "POST":
        if delete_question(question_id):
            messages.success(request, "Question deleted.")
        else:
            messages.error(request, "Question was not found.")
    return redirect("admin_questions")


@admin_required
def admin_notes(request):
    return render(request, "admin/notes.html", {"notes": note_rows()})


@admin_required
def admin_note_create(request):
    form = AdminNoteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        TechnicalNote.objects.update_or_create(
            language_slug=data["language_slug"],
            topic=data["topic"],
            defaults={"language_name": data["language_name"], "content": form.as_content()},
        )
        messages.success(request, "Technical note saved.")
        return redirect("admin_notes")
    return render(request, "admin/note_form.html", {"form": form, "heading": "Add Technical Note"})


@admin_required
def admin_note_edit(request, language_slug, topic_index):
    language = get_languages().get(language_slug)
    if not language or topic_index < 0 or topic_index >= len(language["topics"]):
        raise PermissionDenied("Technical note not found.")
    topic = language["topics"][topic_index]
    note, created = TechnicalNote.objects.get_or_create(
        language_slug=language_slug,
        topic=topic,
        defaults={"language_name": language["name"], "content": language["notes"][topic]},
    )
    form = AdminNoteForm(request.POST or None, initial={"language_name": language["name"], "language_slug": language_slug, "topic": topic}, content=note.content)
    if request.method == "POST" and form.is_valid():
        note.language_name = form.cleaned_data["language_name"]
        note.language_slug = form.cleaned_data["language_slug"]
        note.topic = form.cleaned_data["topic"]
        note.content = form.as_content()
        note.save()
        messages.success(request, "Technical note updated.")
        return redirect("admin_notes")
    return render(request, "admin/note_form.html", {"form": form, "heading": "Edit Technical Note"})


@admin_required
def admin_note_delete(request, language_slug, topic_index):
    language = get_languages().get(language_slug)
    if request.method == "POST" and language and 0 <= topic_index < len(language["topics"]):
        TechnicalNote.objects.filter(language_slug=language_slug, topic=language["topics"][topic_index]).delete()
        messages.success(request, "Technical note override deleted.")
    return redirect("admin_notes")
