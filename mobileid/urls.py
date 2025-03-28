from django.contrib import admin
from django.urls import path
from django.urls import include
from . import views

urlpatterns = [

    # index page
    path("", views.index, name="index"),

    path('settings/', views.settings, name='settings'),

    # user authentication
    path('login/', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout, name='logout'),

    # barcode generation
    path('generate_barcode/', views.generate_code, name='generate_barcode'),

    path('transfer/', views.transfer_key, name='transfer'),
    path('yransfer_code/', views.transfer_code, name='transfer_code'),
]
