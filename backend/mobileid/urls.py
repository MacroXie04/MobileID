from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from barcode.settings import (
    API_ENABLED,
    WEBAPP_ENABLED,
    USER_REGISTRATION_ENABLED,
    API_SERVER,
)
from mobileid.api import (
    webauthn_api,
    user_api,
    barcode_api,
    auth_api,
)
from mobileid.views import (
    webauthn,
    index,
    barcode,
    change_info,
)

app_name = "mobileid"

urlpatterns = []

if API_SERVER:
    urlpatterns += [
        # urlpatterns
        # JWT webauthn api
        path('token/', auth_api.ThrottledTokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

        path('me/', user_api.UserProfileAPIView.as_view(), name='api_user_profile'),

        path('generate_barcode/', barcode_api.GenerateBarcodeView.as_view(), name='api_generate_barcode'),

        path('barcodes/', barcode_api.BarcodeListCreateAPIView.as_view(), name='api_barcode_list_create'),
        path('barcodes/<int:pk>/', barcode_api.BarcodeDestroyAPIView.as_view(), name='api_barcode_destroy'),

        path('barcode_settings/', user_api.BarcodeSettingsAPIView.as_view(), name='api_barcode_settings'),
    ]

    if USER_REGISTRATION_ENABLED:
        urlpatterns += [
            path("register/", webauthn_api.RegisterAPIView.as_view(), name="api_register"),
        ]

else:
    if API_ENABLED:
        urlpatterns += [
            # JWT webauthn api
            path('api/token/', auth_api.ThrottledTokenObtainPairView.as_view(), name='token_obtain_pair'),
            path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

            path('api/me/', user_api.UserProfileAPIView.as_view(), name='api_user_profile'),

            path('api/generate_barcode/', barcode_api.GenerateBarcodeView.as_view(), name='api_generate_barcode'),

            path('api/barcodes/', barcode_api.BarcodeListCreateAPIView.as_view(), name='api_barcode_list_create'),
            path('api/barcodes/<int:pk>/', barcode_api.BarcodeDestroyAPIView.as_view(), name='api_barcode_destroy'),

            path('api/barcode_settings/', user_api.BarcodeSettingsAPIView.as_view(), name='api_barcode_settings'),

        ]
        if USER_REGISTRATION_ENABLED:
            urlpatterns += [
                path("api/register/", webauthn_api.RegisterAPIView.as_view(), name="api_register"),
            ]

    if WEBAPP_ENABLED:
        urlpatterns += [
            # index page
            path("", index.index, name="web_index"),

            # webauthn login
            path("login/", webauthn.web_login, name="web_login"),
            # webauthn logout
            path("logout/", webauthn.web_logout, name="web_logout"),

            # create barcode
            path("manage_barcode/", barcode.create_barcode, name="web_manage_barcode"),
            # generate barcode
            path("generate_barcode/", barcode.generate_barcode, name="web_generate_barcode"),
            path("barcode/delete/<int:pk>/", barcode.delete_barcode, name="web_delete_barcode"),

            # edit profile
            path("edit_profile/", change_info.edit_profile, name="web_edit_profile"),
            # edit barcode settings
            path("barcode_settings/", change_info.edit_barcode_settings, name="web_barcode_settings"),
        ]

        if USER_REGISTRATION_ENABLED:
            urlpatterns += [
                # webauthn registration
                path("register/", webauthn.web_register, name="web_register"),
            ]
