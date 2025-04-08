from django import forms

class BarcodeForm(forms.Form):
    SOURCE_TYPE_CHOICES = [
        ('barcode', 'Barcode'),
        ('session', 'Session'),
        ('transfer_code', 'Transfer Code'),
    ]

    source_type = forms.ChoiceField(
        choices=SOURCE_TYPE_CHOICES,
        label="Barcode Type",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    input_value = forms.CharField(
        label="Enter Value",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter barcode/session/transfer code'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        source_type = cleaned_data.get("source_type")
        input_value = cleaned_data.get("input_value")

        if not input_value:
            raise forms.ValidationError("Please enter a value.")

        if source_type == 'barcode' and not input_value.isdigit():
            raise forms.ValidationError("Barcode only accepts digits.")

        return cleaned_data