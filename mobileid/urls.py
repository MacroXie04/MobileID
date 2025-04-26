from django.urls import path
from .views import index, manage_profile, generate_code, transfer

urlpatterns = [

    # index page
    path("", index.index, name="index"),

    # manage profile
    path('setup/', manage_profile.setup, name='setup'),
    path('settings/', manage_profile.settings, name='settings'),

    # barcode generation
    path('generate_barcode/', generate_code.generate_code, name='generate_barcode'),

    # manage barcode
    path('transfer/', transfer.transfer_key, name='transfer'),
    path('create_barcode/', manage_profile.create_barcode, name='create_barcode'),
    path('manage_barcode/', manage_profile.manage_barcode, name='manage_barcode'),
]

