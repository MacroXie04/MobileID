from django import forms


# transfer code form
class TransferCodeForm(forms.Form):
    transfer_code = forms.CharField(
        max_length=6,
        min_length=6,
        required=True,
        label="TransferCode",
        widget=forms.TextInput(attrs={'class': 'form-control', 'maxlength': '6'})
    )

    def clean_transfer_code(self):
        code = self.cleaned_data.get('transfer_code')
        if not code.isdigit():
            raise forms.ValidationError("TransferCode must be a 6-digit number.")
        return code
