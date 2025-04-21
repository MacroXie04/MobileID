from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DeleteView
from django.urls import reverse_lazy
from webauthn_app.models import PasskeyCredential

@method_decorator(login_required, name='dispatch')
class PasskeyListView(ListView):
    model = PasskeyCredential
    context_object_name = 'passkeys'
    template_name = 'manage/manage_passkeys.html'

    def get_queryset(self):
        return PasskeyCredential.objects.filter(user=self.request.user)


@method_decorator(login_required, name='dispatch')
class PasskeyDeleteView(DeleteView):
    model = PasskeyCredential
    success_url = reverse_lazy('manage_passkeys')
    template_name = 'manage/delete_passkey.html'

    def get_queryset(self):
        return PasskeyCredential.objects.filter(user=self.request.user)