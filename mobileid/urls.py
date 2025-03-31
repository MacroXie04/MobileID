from django.urls import path
from .views import user_verification, index, manage_profile, generate_code, transfer
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    # index page
    path("", index.index, name="index"),

    # settings page
    path('setup/', manage_profile.setup, name='setup'),
    path('settings/', manage_profile.settings, name='settings'),

    # user authentication
    path('login/', user_verification.user_login, name='login'),
    path('register/', user_verification.register, name='register'),
    path('logout/', user_verification.logout, name='logout'),

    # barcode generation
    path('generate_barcode/', generate_code.generate_code, name='generate_barcode'),

    # barcode transfer
    path('transfer/', transfer.transfer_key, name='transfer'),
    path('transfer_code/', transfer.transfer_code, name='transfer_code'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
