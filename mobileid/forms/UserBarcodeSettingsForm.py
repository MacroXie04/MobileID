from django import forms
from mobileid.models import UserBarcodeSettings


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
        if self.instance and self.instance.pk:
            self.fields['barcode_status'].initial = 'True' if self.instance.barcode_status else 'False'
            self.fields['server_verification'].initial = 'True' if self.instance.server_verification else 'False'

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.barcode_status = (self.cleaned_data['barcode_status'] == 'True')
        instance.server_verification = (self.cleaned_data['server_verification'] == 'True')
        if commit:
            instance.save()
        return instance
