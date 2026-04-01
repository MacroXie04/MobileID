from rest_framework import status
from rest_framework.response import Response

from index.repositories import BarcodeRepository, SettingsRepository
from index.serializers import BarcodeSerializer, BarcodeCreateSerializer
from index.services.transactions import TransactionService


class DashboardBarcodeCRUDMixin:
    """PUT/PATCH/DELETE handlers: barcode create, update, and delete."""

    def put(self, request):
        """Create new barcode"""
        serializer = BarcodeCreateSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            barcode = serializer.save()
            # Record a transaction for barcode creation
            TransactionService.create_transaction(user=request.user, barcode=barcode)
            return Response(
                {
                    "status": "success",
                    "message": "New barcode added successfully",
                    "barcode": BarcodeSerializer(
                        barcode, context={"request": request}
                    ).data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"status": "error", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def patch(self, request):
        """Update properties of a barcode owned by the current user."""
        barcode_id = request.data.get("barcode_id")
        share_with_others = request.data.get("share_with_others")
        daily_usage_limit = request.data.get("daily_usage_limit")

        if not barcode_id:
            return Response(
                {"status": "error", "message": "barcode_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Look up barcode by UUID (barcode_id is now UUID)
        barcode = BarcodeRepository.get_by_uuid(request.user.id, barcode_id)
        if not barcode:
            return Response(
                {
                    "status": "error",
                    "message": "Barcode not found or you do not have "
                    "permission to update it",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        updates = {}

        # Update share_with_others if provided
        if share_with_others is not None:
            if isinstance(share_with_others, str):
                share_with_others = share_with_others.lower() in [
                    "1", "true", "yes", "on",
                ]
            updates["share_with_others"] = bool(share_with_others)

        # Update daily_usage_limit if provided
        if daily_usage_limit is not None:
            try:
                limit_value = int(daily_usage_limit)
                if limit_value < 0:
                    return Response(
                        {
                            "status": "error",
                            "message": "Daily usage limit must be 0 or greater",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                updates["daily_usage_limit"] = limit_value
            except (ValueError, TypeError):
                return Response(
                    {
                        "status": "error",
                        "message": "Daily usage limit must be a valid number",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if updates:
            barcode = BarcodeRepository.update(
                user_id=request.user.id,
                barcode_uuid=barcode_id,
                **updates,
            )

        return Response(
            {
                "status": "success",
                "message": "Barcode updated successfully",
                "barcode": BarcodeSerializer(
                    barcode, context={"request": request}
                ).data,
            }
        )

    def delete(self, request):
        """Delete barcode - users may only delete their own DynamicBarcode/Others."""
        barcode_id = request.data.get("barcode_id")

        if not barcode_id:
            return Response(
                {"status": "error", "message": "Barcode ID is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Look up barcode by UUID
        barcode = BarcodeRepository.get_by_uuid(request.user.id, barcode_id)
        if not barcode or barcode.get("barcode_type") not in [
            "DynamicBarcode", "Others",
        ]:
            return Response(
                {
                    "status": "error",
                    "message": "Barcode not found or you do not have "
                    "permission to delete it",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Clear from settings if currently selected
        SettingsRepository.clear_barcode_if_matches(request.user.id, barcode_id)

        BarcodeRepository.delete(
            user_id=request.user.id,
            barcode_uuid=barcode_id,
        )

        return Response(
            {"status": "success", "message": "Barcode deleted successfully"}
        )
