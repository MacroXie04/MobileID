from django.urls import path
from rest_framework_simplejwt.views import (TokenRefreshView)

from barcode.settings import (API_SERVER)
from mobileid.api import auth_api, barcode_api, user_api, webauthn_api
from mobileid.views import (barcode, change_info, health, index, webauthn, manage)

app_name = "mobileid"

urlpatterns = []

if API_SERVER:
    urlpatterns += [
        # urlpatterns
        # JWT webauthn api
        path(
            "token/",
            auth_api.ThrottledTokenObtainPairView.as_view(),
            name="token_obtain_pair",
        ),
        path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
        path("me/", user_api.UserProfileAPIView.as_view(), name="api_user_profile"),
        path(
            "generate_barcode/",
            barcode_api.GenerateBarcodeView.as_view(),
            name="api_generate_barcode",
        ),
        path(
            "barcodes/",
            barcode_api.BarcodeListCreateAPIView.as_view(),
            name="api_barcode_list_create",
        ),
        path(
            "barcodes/<int:pk>/",
            barcode_api.BarcodeDestroyAPIView.as_view(),
            name="api_barcode_destroy",
        ),
        path(
            "barcode_settings/",
            user_api.BarcodeSettingsAPIView.as_view(),
            name="api_barcode_settings",
        ),
        path(
            "register/", webauthn_api.RegisterAPIView.as_view(), name="api_register"
        ),
    ]


else:
    urlpatterns += [
        # index page
        path("", index.index, name="web_index"),
        # webauthn login
        path("login/", webauthn.web_login, name="web_login"),
        # webauthn logout
        path("logout/", webauthn.web_logout, name="web_logout"),
        # generate barcode
        path(
            "generate_barcode/",
            barcode.generate_barcode_view,
            name="web_generate_barcode",
        ),
        # edit profile
        path("edit_profile/", change_info.edit_profile, name="web_edit_profile"),




        # edit barcode settings
        path(
            "barcode_settings/",
            manage.manage_barcode,
            name="web_barcode_settings",
        ),

        path('delete-barcode/<int:barcode_id>/', manage.delete_barcode, name='web_delete_barcode'),

        path('barcode-info/<int:barcode_id>/', manage.get_barcode_info, name='web_barcode_info'),


        # webauthn registration
        path("register/", webauthn.web_register, name="web_register"),
    ]


# Health check endpoint (always available)
urlpatterns += [
    path("health/", health.health_check, name="health_check"),
]
