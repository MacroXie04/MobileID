from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from index.serializers import (
    BarcodeSerializer,
    DynamicBarcodeWithProfileSerializer,
)
from index.services.transactions import TransactionService


class DynamicBarcodeCreateAPIView(APIView):
    """
    API endpoint for creating dynamic barcodes with profile information.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Create a new dynamic barcode with profile data"""
        serializer = DynamicBarcodeWithProfileSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            barcode = serializer.save()
            # Record a transaction for barcode creation
            TransactionService.create_transaction(user=request.user, barcode=barcode)

            return Response(
                {
                    "status": "success",
                    "message": "Dynamic barcode with profile created successfully",
                    "barcode": BarcodeSerializer(
                        barcode, context={"request": request}
                    ).data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "status": "error",
                "message": "Invalid request data",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
