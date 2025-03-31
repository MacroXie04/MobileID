from django import forms


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
    avatar = forms.ImageField(
        label="Profile Photo",
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
        })
    )
    session = forms.CharField(
        label="Session",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your Session (no limit)'
        })
    )
