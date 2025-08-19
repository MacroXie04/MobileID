# url patterns for index

from django.urls import path

from index.api.barcode import GenerateBarcodeAPIView
from index.api.dashboard import BarcodeDashboardAPIView

app_name = "index"

urlpatterns = [
    # generate barcode api
    path("generate_barcode/", GenerateBarcodeAPIView.as_view(), name="api_generate_barcode"),

    # barcode dashboard
    path("barcode_dashboard/", BarcodeDashboardAPIView.as_view(), name="api_barcode_dashboard"),
]
