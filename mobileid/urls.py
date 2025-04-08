from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from .views import user_verification, index, manage_profile, generate_code, transfer

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

    # create barcode
    path('transfer/', transfer.transfer_key, name='transfer'),
    path('create_barcode/', manage_profile.create_barcode, name='create_barcode'),
]

