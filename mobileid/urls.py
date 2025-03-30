from django.contrib import admin
from django.urls import path
from django.urls import include
from .views import user_verification, index, settings, generate_code, transfer

urlpatterns = [

    # index page
    path("", index.index, name="index"),

    # settings page
    path('setup/', settings.setup, name='setup'),
    path('settings/', settings.settings, name='settings'),

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
