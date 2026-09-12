from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import ContactSubmission


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)


class QuizSelectionForm(forms.Form):
    SUBJECT_CHOICES = [
        ("Python", "Python"),
        ("SQL", "SQL"),
        ("PostgreSQL", "PostgreSQL"),
        ("DBMS", "DBMS"),
        ("OOP", "OOP"),
        ("Data Structures", "Data Structures"),
        ("Operating Systems", "Operating Systems"),
        ("Computer Networks", "Computer Networks"),
    ]

    subject = forms.ChoiceField(choices=SUBJECT_CHOICES)
    topic = forms.CharField(max_length=100)


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactSubmission
        fields = ["name", "email", "subject", "message"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 7}),
        }
