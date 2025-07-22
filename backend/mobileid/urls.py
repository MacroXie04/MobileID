from django.urls import path
from barcode.settings import (API_SERVER)
from mobileid.views import (index, manage)
from authn.views import change_info
from mobileid.api.barcode import GenerateBarcodeAPIView

app_name = "mobileid"

urlpatterns = []

if API_SERVER:
    urlpatterns += [
        # generate barcode api
        path("generate_barcode/", GenerateBarcodeAPIView.as_view(), name="api_generate_barcode"),
    ]

else:
    urlpatterns += [
        # index page
        path("", index.index, name="web_index"),

        # generate barcode
        path(
            "generate_barcode/",
            index.generate_barcode_view,
            name="web_generate_barcode",
        ),

        # edit barcode settings
        path(
            "barcode_dashboard/",
            manage.barcode_dashboard,
            name="web_barcode_dashboard",
        ),
    ]

