import base64
from io import BytesIO

from PIL import Image
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from mobileid.models import UserProfile


# UserLoginForm
class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Username',
        max_length=150,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter your username'
            }
        )
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter your password'
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if self.errors.get(field_name):
                field.widget.attrs['class'] += ' is-invalid'


# user registration form
class UserRegisterForm(UserCreationForm):
    name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name'})
    )
    student_id = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Student ID'})
    )
    user_profile_img = forms.ImageField(
        required=True,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'name', 'id', 'user_profile_img']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your username'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name'}),
            'id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Student ID'}),
            'user_profile_img': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super(UserRegisterForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-control'

            if self.errors.get(field_name):
                field.widget.attrs['class'] += ' is-invalid'

    def save(self, commit=True):
        # Save the User instance first
        user = super().save(commit=commit)

        # Gather extra form data
        name = self.cleaned_data['name']
        student_id = self.cleaned_data['id']
        img_file = self.cleaned_data['user_profile_img']

        # -------------------------------
        # Process avatar -> 128×128 PNG
        # -------------------------------
        with Image.open(img_file) as im:
            min_side = min(im.size)
            left = (im.width - min_side) // 2
            top = (im.height - min_side) // 2
            im = im.crop((left, top, left + min_side, top + min_side))
            im = im.resize((128, 128), Image.LANCZOS)

            buffer = BytesIO()
            im.save(buffer, format='PNG')
            base64_img = base64.b64encode(buffer.getvalue()).decode('utf-8')

        # Create UserProfile
        UserProfile.objects.create(
            user=user,
            name=name,
            student_id=student_id,
            user_profile_img=base64_img,
        )

        return user
