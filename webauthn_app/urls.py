# urls.py for webauthn_app
from django.urls import path, include
from .views import passkeys, manage, user_verification

app_name = "webauthn_app"


passkey_patterns = [
    path('reg/options',   passkeys.register_options, name='reg_options'),
    path('reg/complete',  passkeys.register_complete, name='reg_complete'),
    path('auth/options',  passkeys.auth_options,     name='auth_options'),
    path('auth/complete', passkeys.auth_complete,    name='auth_complete'),

    path('', manage.PasskeyListView.as_view(), name='manage_passkeys'),
    path('delete/<int:pk>/', manage.PasskeyDeleteView.as_view(), name='delete_passkey'),
]

urlpatterns = [
    # Illegal request handling
    path('reject/', user_verification.illegal_request, name='illegal_request'),

    # Login view for the webauthn app
    path('passkey/', include(passkey_patterns)),


    # user authentication
    path('login/', user_verification.user_login, name='login'),
    path('register/', user_verification.register, name='register'),
    path('logout/', user_verification.logout, name='logout'),

    # Account management views
    path('', manage.manage_account, name='manage_account'),
    path('password/', manage.change_password, name='manage_password'),
]
