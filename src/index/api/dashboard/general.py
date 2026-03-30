from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from index.api.dashboard.barcode_crud import DashboardBarcodeCRUDMixin
from index.api.dashboard.retrieve import DashboardRetrieveMixin
from index.api.dashboard.settings_update import DashboardSettingsUpdateMixin


class BarcodeDashboardAPIView(
    DashboardRetrieveMixin,
    DashboardSettingsUpdateMixin,
    DashboardBarcodeCRUDMixin,
    APIView,
):
    """
    API endpoint for barcode dashboard functionality:
    - GET: Retrieve user settings and barcodes
    - POST: Update settings
    - PUT: Create new barcode
    - PATCH: Update barcode properties
    - DELETE: Delete barcode

    Business rules:
    1. When associate_user_profile_with_barcode is True, barcode field must be disabled and cleared  # noqa: E501
    2. Only DynamicBarcode and Others types can be managed
    """

    permission_classes = [IsAuthenticated]
