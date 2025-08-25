# url patterns for index

from django.urls import path

from index.api.barcode import GenerateBarcodeAPIView, ActiveProfileAPIView
from index.api.dashboard import BarcodeDashboardAPIView
from index.api.transfer import TransferCatCardAPIView

app_name = "index"

urlpatterns = [
    # generate barcode api
    path("generate_barcode/", GenerateBarcodeAPIView.as_view(), name="api_generate_barcode"),
    
    # get active profile based on settings
    path("active_profile/", ActiveProfileAPIView.as_view(), name="api_active_profile"),

    # barcode dashboard
    path("barcode_dashboard/", BarcodeDashboardAPIView.as_view(), name="api_barcode_dashboard"),

    # transfer catcard endpoint
    path("transfer/", TransferCatCardAPIView.as_view(), name="api_catcard_transfer"),
]