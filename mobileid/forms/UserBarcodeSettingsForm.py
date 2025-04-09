from django import forms

from mobileid.models import UserBarcodeSettings, Barcode


class UserBarcodeSettingsForm(forms.ModelForm):
    barcode = forms.ModelChoiceField(
        queryset=Barcode.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Barcode'
    )
    # 布尔类型字段使用 TypedChoiceField 以下拉框显示 Enabled/Disabled 选项
    server_verification = forms.TypedChoiceField(
        choices=[('True', 'Enabled'), ('False', 'Disabled')],
        coerce=lambda x: x == 'True',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Server Verification'
    )
    timestamp_verification = forms.TypedChoiceField(
        choices=[('True', 'Enabled'), ('False', 'Disabled')],
        coerce=lambda x: x == 'True',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Timestamp Verification'
    )
    dynamic_barcode = forms.TypedChoiceField(
        choices=[('True', 'Enabled'), ('False', 'Disabled')],
        coerce=lambda x: x == 'True',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Dynamic Barcode'
    )
    barcode_pull = forms.TypedChoiceField(
        choices=[('True', 'Enabled'), ('False', 'Disabled')],
        coerce=lambda x: x == 'True',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Barcode Pull'
    )

    class Meta:
        model = UserBarcodeSettings
        fields = [
            'barcode',
            'server_verification',
            'timestamp_verification',
            'dynamic_barcode',
            'barcode_pull'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['server_verification'].initial = 'True' if self.instance.server_verification else 'False'
            self.fields['timestamp_verification'].initial = 'True' if self.instance.timestamp_verification else 'False'
            self.fields['dynamic_barcode'].initial = 'True' if self.instance.dynamic_barcode else 'False'
            self.fields['barcode_pull'].initial = 'True' if self.instance.barcode_pull else 'False'

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.server_verification = self.cleaned_data['server_verification']
        instance.timestamp_verification = self.cleaned_data['timestamp_verification']
        instance.dynamic_barcode = self.cleaned_data['dynamic_barcode']
        instance.barcode_pull = self.cleaned_data['barcode_pull']
        if commit:
            instance.save()
        return instance
