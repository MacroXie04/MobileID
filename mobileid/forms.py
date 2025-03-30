from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import UserBarcodeSettings

class UserRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your username'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}),
        }

    def __init__(self, *args, **kwargs):
        super(UserRegisterForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-control'

            if self.errors.get(field_name):
                field.widget.attrs['class'] += ' is-invalid'

# user login
class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username",
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your username'})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'})
    )

    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if self.errors.get(field_name):
                field.widget.attrs['class'] += ' is-invalid'

# settings form
class SettingsForm(forms.Form):
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

# barcode settings form
class UserBarcodeSettingsForm(forms.ModelForm):
    barcode_status = forms.ChoiceField(
        choices=[('True', 'Enabled'), ('False', 'Disabled')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Static Barcode'
    )
    server_verification = forms.ChoiceField(
        choices=[('True', 'Enabled'), ('False', 'Disabled')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='CatCard Server verification'
    )

    class Meta:
        model = UserBarcodeSettings
        fields = ['barcode_status', 'static_barcode', 'server_verification']
        widgets = {
            'static_barcode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your static barcode'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 如果是编辑已有记录，根据数据库布尔值设置初始选项
        if self.instance and self.instance.pk:
            self.fields['barcode_status'].initial = 'True' if self.instance.barcode_status else 'False'
            self.fields['server_verification'].initial = 'True' if self.instance.server_verification else 'False'

    def save(self, commit=True):
        instance = super().save(commit=False)
        # 将 'True'/'False' 转回布尔值
        instance.barcode_status = (self.cleaned_data['barcode_status'] == 'True')
        instance.server_verification = (self.cleaned_data['server_verification'] == 'True')
        if commit:
            instance.save()
        return instance