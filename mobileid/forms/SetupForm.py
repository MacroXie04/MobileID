from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User


# setup form
class SetupForm(forms.Form):
    name = forms.CharField(label="Full Name", max_length=100, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your full name'
    }))
    student_id = forms.CharField(label="Student ID", max_length=20, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your student ID'
    }))
    session = forms.CharField(
        label="Session",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your Session (no limit)'
        })
    )