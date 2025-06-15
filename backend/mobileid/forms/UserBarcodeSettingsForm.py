from django import forms
from mobileid.models import UserBarcodeSettings, Barcode


class UserBarcodeSettingsForm(forms.ModelForm):
    barcode = forms.ModelChoiceField(
        queryset=Barcode.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Barcode'
    )

    # server_verification
    server_verification = forms.TypedChoiceField(
        choices=[('True', 'Enabled'), ('False', 'Disabled')],
        coerce=lambda x: x == 'True',
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Server Verification'
    )

    # timestamp_verification
    timestamp_verification = forms.TypedChoiceField(
        choices=[('True', 'Enabled'), ('False', 'Disabled')],
        coerce=lambda x: x == 'True',
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Timestamp Verification'
    )

    # barcode_pull
    barcode_pull = forms.TypedChoiceField(
        choices=[('True', 'Enabled'), ('False', 'Disabled')],
        coerce=lambda x: x == 'True',
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Barcode Pull'
    )

    class Meta:
        model = UserBarcodeSettings
        fields = [
            'barcode',
            'server_verification',
            'timestamp_verification',
            'barcode_pull'
        ]

    def __init__(self, *args, **kwargs):
        # 从关键字参数中取出当前登录的用户
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # 如果传入了user，则只显示该用户对应的Barcode记录
        if user:
            self.fields['barcode'].queryset = Barcode.objects.filter(user=user)

        # 初始化其它字段的默认状态
        if self.instance.pk:
            self.fields['server_verification'].initial = 'True' if self.instance.server_verification else 'False'
            self.fields['timestamp_verification'].initial = 'True' if self.instance.timestamp_verification else 'False'
            self.fields['barcode_pull'].initial = 'True' if self.instance.barcode_pull else 'False'

        barcode_instance = self.instance.barcode

        if self.instance.barcode_pull:
            self.fields['barcode'].widget.attrs['disabled'] = True
            self.fields['server_verification'].widget.attrs['disabled'] = True
            self.fields['timestamp_verification'].widget.attrs['disabled'] = True

        elif barcode_instance and barcode_instance.barcode_type == 'Static':
            self.fields['server_verification'].widget.attrs['disabled'] = True
            self.fields['timestamp_verification'].widget.attrs['disabled'] = True

    def clean(self):
        cleaned_data = super().clean()
        barcode_pull = cleaned_data.get("barcode_pull")
        barcode = cleaned_data.get("barcode")

        if barcode_pull is False and not barcode:
            raise forms.ValidationError("You must select a barcode if barcode pull is disabled.")

        if barcode_pull:
            cleaned_data['barcode'] = None
            cleaned_data['server_verification'] = self.instance.server_verification
            cleaned_data['timestamp_verification'] = self.instance.timestamp_verification

        if barcode and barcode.barcode_type == 'Static':
            cleaned_data['server_verification'] = self.instance.server_verification
            cleaned_data['timestamp_verification'] = self.instance.timestamp_verification

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.server_verification = self.cleaned_data['server_verification']
        instance.timestamp_verification = self.cleaned_data['timestamp_verification']
        instance.barcode_pull = self.cleaned_data['barcode_pull']

        if instance.barcode_pull:
            instance.barcode = None

        if commit:
            instance.save()
        return instance