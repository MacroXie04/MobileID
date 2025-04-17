# urls.py for webauthn_app
from django.urls import path
from . import views

app_name = "webauthn_app"
urlpatterns = [
    # Login view for the webauthn app
    path('reg/options', views.register_options, name='reg_options'),
    path('reg/complete', views.register_complete, name='reg_complete'),
    path('auth/options', views.auth_options, name='auth_options'),
    path('auth/complete', views.auth_complete, name='auth_complete'),
]
