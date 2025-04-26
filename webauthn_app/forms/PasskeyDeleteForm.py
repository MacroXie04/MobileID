from django import forms

class PasskeyDeleteForm(forms.Form):
    passkey_id = forms.IntegerField(widget=forms.HiddenInput())