from django import forms
from mobileid.models import Barcode

class ManageBarcodeForm(forms.Form):
    barcode = forms.ModelChoiceField(
        queryset=Barcode.objects.none(),
        empty_label="Please select a Barcode to delete",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['barcode'].queryset = Barcode.objects.filter(user=user)