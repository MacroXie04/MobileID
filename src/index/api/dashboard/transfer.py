from rest_framework import status, serializers as drf_serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from index.serializers import (
    BarcodeSerializer,
    DynamicBarcodeWithProfileSerializer,
)
from index.services.transactions import TransactionService
from index.services.transfer_barcode import TransferBarcodeParser


class TransferDynamicBarcodeAPIView(APIView):
    """
    API endpoint for creating dynamic barcodes by parsing HTML content.
    Only School group users can use this endpoint.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Parse HTML and create a new dynamic barcode with profile data"""
        # Check if user is in School group
        if not request.user.groups.filter(name="School").exists():
            return Response(
                {
                    "status": "error",
                    "message": "Only School group users can transfer dynamic barcodes",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get HTML from request
        html_content = request.data.get("html")
        if not html_content:
            return Response(
                {
                    "status": "error",
                    "errors": {"html": ["HTML content is required"]},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Parse HTML using TransferBarcodeParser
        parser = TransferBarcodeParser()
        parsed_data = parser.parse(html_content)

        # Validate parsed data - check required fields
        errors = {}
        if not parsed_data.get("barcode"):
            errors["barcode"] = ["Could not extract barcode from HTML"]
        if not parsed_data.get("name"):
            errors["name"] = ["Could not extract name from HTML"]
        if not parsed_data.get("information_id"):
            errors["information_id"] = ["Could not extract student ID from HTML"]

        if errors:
            return Response(
                {
                    "status": "error",
                    "message": "Could not parse required fields from HTML",
                    "errors": errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Build serializer data
        serializer_data = {
            "barcode": parsed_data["barcode"],
            "name": parsed_data["name"],
            "information_id": parsed_data["information_id"],
            "gender": "Unknow",  # Default gender since HTML doesn't contain it
        }

        # Include avatar if extracted (already base64 without prefix)
        if parsed_data.get("img_base64"):
            serializer_data["avatar"] = parsed_data["img_base64"]

        serializer = DynamicBarcodeWithProfileSerializer(
            data=serializer_data, context={"request": request}
        )

        if serializer.is_valid():
            try:
                barcode = serializer.save()
            except drf_serializers.ValidationError as e:
                # Handle validation errors raised in create()
                return Response(
                    {
                        "status": "error",
                        "message": "Barcode validation failed",
                        "errors": e.detail,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Record a transaction for barcode creation
            TransactionService.create_transaction(user=request.user, barcode=barcode)

            return Response(
                {
                    "status": "success",
                    "message": "Dynamic barcode transferred successfully",
                    "barcode": BarcodeSerializer(
                        barcode, context={"request": request}
                    ).data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "status": "error",
                "message": "Invalid barcode data",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
