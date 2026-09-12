import json

from django import forms

from .admin_content import COMPANY_CHOICES, question_choices, topic_choices


class AdminLoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)


class AdminQuestionForm(forms.Form):
    subject = forms.ChoiceField(choices=question_choices())
    topic = forms.ChoiceField(choices=[(topic, topic) for topic in topic_choices()])
    company = forms.ChoiceField(choices=[(choice, choice) for choice in COMPANY_CHOICES], required=False)
    year = forms.IntegerField(required=False, min_value=1900, max_value=2100)
    difficulty = forms.ChoiceField(choices=[("Easy", "Easy"), ("Medium", "Medium"), ("Hard", "Hard")])
    question = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}))
    option_a = forms.CharField(max_length=255)
    option_b = forms.CharField(max_length=255)
    option_c = forms.CharField(max_length=255)
    option_d = forms.CharField(max_length=255)
    correct_answer = forms.ChoiceField(choices=[("A", "Option A"), ("B", "Option B"), ("C", "Option C"), ("D", "Option D")])
    explanation = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}))
    hint = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))

    def clean(self):
        cleaned = super().clean()
        options = [cleaned.get(f"option_{letter.lower()}") for letter in "ABCD"]
        if all(options) and len(set(options)) != 4:
            raise forms.ValidationError("All four options must be different.")
        return cleaned

    def as_question_data(self):
        data = self.cleaned_data
        result = {
            "question": data["question"].strip(),
            "options": {letter: data[f"option_{letter.lower()}"].strip() for letter in "ABCD"},
            "correct_answer": data["correct_answer"],
            "explanation": data["explanation"].strip(),
            "difficulty": data["difficulty"],
            "company": data.get("company") or "General",
            "year": data.get("year") or "",
            "hint": data.get("hint", "").strip(),
        }
        return result


class AdminNoteForm(forms.Form):
    language_name = forms.CharField(max_length=100)
    language_slug = forms.SlugField(max_length=100)
    topic = forms.CharField(max_length=150)
    overview = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}))
    core_concepts = forms.CharField(widget=forms.Textarea(attrs={"rows": 5}), help_text="One point per line.")
    syntax = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}), required=False)
    examples = forms.CharField(widget=forms.Textarea(attrs={"rows": 8}), help_text="JSON list of example objects.")
    important = forms.CharField(widget=forms.Textarea(attrs={"rows": 5}), help_text="One point per line.")
    mistakes = forms.CharField(widget=forms.Textarea(attrs={"rows": 5}), help_text="One point per line.")
    interview = forms.CharField(widget=forms.Textarea(attrs={"rows": 8}), help_text="JSON list of question/answer objects.")
    exam_points = forms.CharField(widget=forms.Textarea(attrs={"rows": 5}), help_text="One point per line.")
    revision = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))
    practice = forms.CharField(widget=forms.Textarea(attrs={"rows": 5}), help_text="One question per line.")

    def clean_json_list(self, field_name):
        try:
            value = json.loads(self.cleaned_data[field_name])
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            raise forms.ValidationError("Enter a valid JSON list.") from error
        if not isinstance(value, list):
            raise forms.ValidationError("This value must be a JSON list.")
        return value

    def clean_examples(self):
        return self.clean_json_list("examples")

    def clean_interview(self):
        return self.clean_json_list("interview")

    def as_content(self):
        data = self.cleaned_data
        return {
            "overview": data["overview"],
            "core_concepts": [item.strip() for item in data["core_concepts"].splitlines() if item.strip()],
            "syntax": data["syntax"],
            "examples": data["examples"],
            "important": [item.strip() for item in data["important"].splitlines() if item.strip()],
            "mistakes": [item.strip() for item in data["mistakes"].splitlines() if item.strip()],
            "interview": data["interview"],
            "exam_points": [item.strip() for item in data["exam_points"].splitlines() if item.strip()],
            "revision": data["revision"],
            "practice": [item.strip() for item in data["practice"].splitlines() if item.strip()],
        }

    def __init__(self, *args, content=None, **kwargs):
        super().__init__(*args, **kwargs)
        if content and not self.is_bound:
            self.initial.update({
                "overview": content.get("overview", ""),
                "core_concepts": "\n".join(content.get("core_concepts", [])),
                "syntax": content.get("syntax", ""),
                "examples": json.dumps(content.get("examples", []), indent=2),
                "important": "\n".join(content.get("important", [])),
                "mistakes": "\n".join(content.get("mistakes", [])),
                "interview": json.dumps(content.get("interview", []), indent=2),
                "exam_points": "\n".join(content.get("exam_points", [])),
                "revision": content.get("revision", ""),
                "practice": "\n".join(content.get("practice", [])),
            })
