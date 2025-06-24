from django import forms

class BarcodeForm(forms.Form):
    SOURCE_TYPE_CHOICES = [
        ('barcode', 'Barcode'),
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add 'is-invalid' class to fields with errors for styling red borders
        for field in self.fields:
            if self.errors.get(field):
                existing_classes = self.fields[field].widget.attrs.get('class', '')
                if 'is-invalid' not in existing_classes:
                    self.fields[field].widget.attrs['class'] = existing_classes + ' is-invalid'

    def clean(self):
        cleaned_data = super().clean()
        source_type = cleaned_data.get("source_type")
        input_value = cleaned_data.get("input_value")

        if not input_value:
            raise forms.ValidationError("Please enter a value.")

        if source_type == 'barcode' and not input_value.isdigit():
            raise forms.ValidationError("Barcode only accepts digits.")

        return cleaned_data