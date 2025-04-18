# urls.py for webauthn_app
from django.urls import path
from .views import passkeys

app_name = "webauthn_app"
urlpatterns = [
    # Login view for the webauthn app
    path('reg/options', passkeys.register_options, name='reg_options'),
    path('reg/complete', passkeys.register_complete, name='reg_complete'),
    path('auth/options', passkeys.auth_options, name='auth_options'),
    path('auth/complete', passkeys.auth_complete, name='auth_complete'),
]
