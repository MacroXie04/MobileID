# url patterns for index

from django.urls import path

from index.api.barcode import GenerateBarcodeAPIView, ActiveProfileAPIView
from index.api.dashboard import BarcodeDashboardAPIView, DynamicBarcodeCreateAPIView

app_name = "index"

urlpatterns = [
    # generate barcode api
    path(
        "generate_barcode/",
        GenerateBarcodeAPIView.as_view(),
        name="api_generate_barcode",
    ),
    # get active profile based on settings
    path(
        "active_profile/",
        ActiveProfileAPIView.as_view(),
        name="api_active_profile",
    ),
    # barcode dashboard
    path(
        "barcode_dashboard/",
        BarcodeDashboardAPIView.as_view(),
        name="api_barcode_dashboard",
    ),
    # create dynamic barcode with profile
    path(
        "dynamic_barcode/",
        DynamicBarcodeCreateAPIView.as_view(),
        name="api_dynamic_barcode_create",
    ),
]
