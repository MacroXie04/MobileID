from django.urls import path

from mobileid.api.barcode import GenerateBarcodeAPIView
from mobileid.api.dashboard import BarcodeDashboardAPIView

app_name = "mobileid"

urlpatterns = [
    # generate barcode api
    path("generate_barcode/", GenerateBarcodeAPIView.as_view(), name="api_generate_barcode"),

    # barcode dashboard
    path("barcode_dashboard/", BarcodeDashboardAPIView.as_view(), name="api_barcode_dashboard"),
]