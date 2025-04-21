from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm


class PasswordChangeForm(DjangoPasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fieldname in ['old_password', 'new_password1', 'new_password2']:
            self.fields[fieldname].widget.attrs.update({'class': 'form-control mb-2'})
            self.fields[fieldname].help_text = None
