from django import forms
from mobileid.models import Barcode, UserAccount, UserBarcodeSettings


class CombinedBarcodeForm(forms.Form):
    # Barcode model fields
    barcode_type = forms.ChoiceField(
        choices=Barcode.BARCODE_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    barcode = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter barcode value'
        })
    )

    VERIFICATION_CHOICES = [
        (True, 'Enabled'),
        (False, 'Disabled')
    ]

    server_verification = forms.ChoiceField(
        choices=VERIFICATION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )

    timestamp_verification = forms.ChoiceField(
        choices=VERIFICATION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )

    barcode_pull = forms.ChoiceField(
        choices=VERIFICATION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )

    # choice field for existing barcodes
    barcode_choice = forms.ModelChoiceField(
        queryset=Barcode.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Select a barcode"
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        if user:
            user_account = UserAccount.objects.get(user=user)

            if user_account.account_type == 'User':
                self.fields['barcode_type'].choices = [('Others', 'Others')]
                self.fields['barcode_type'].initial = 'Others'

                # User 类型只能选择条码，其他设置不可见
                self.fields['server_verification'].widget = forms.HiddenInput()
                self.fields['timestamp_verification'].widget = forms.HiddenInput()
                self.fields['barcode_pull'].widget = forms.HiddenInput()
                self.fields['barcode_choice'].queryset = Barcode.objects.filter(user=user)


            elif user_account.account_type == 'School':
                self.fields['barcode_type'].choices = [
                    ('Others', 'Others'),
                    ('DynamicBarcode', 'DynamicBarcode')
                ]
                self.fields['barcode_choice'].queryset = Barcode.objects.filter(user=user)

    def clean(self):
        cleaned_data = super().clean()
        barcode_type = cleaned_data.get('barcode_type')
        barcode = cleaned_data.get('barcode')
        barcode_choice = cleaned_data.get('barcode_choice')

        # 将选择框的值转换为布尔类型
        if 'server_verification' in cleaned_data:
            cleaned_data['server_verification'] = cleaned_data['server_verification'] == 'True'

        if 'timestamp_verification' in cleaned_data:
            cleaned_data['timestamp_verification'] = cleaned_data['timestamp_verification'] == 'True'

        if 'barcode_pull' in cleaned_data:
            cleaned_data['barcode_pull'] = cleaned_data['barcode_pull'] == 'True'

        # 验证逻辑
        if barcode_type and barcode:
            if Barcode.objects.filter(barcode=barcode).exists():
                self.add_error('barcode', 'This barcode already exists.')

        # 确保必填字段
        if self.user.account_type == 'User' and not barcode_choice:
            self.add_error('barcode_choice', 'Please select a barcode.')

        return cleaned_data