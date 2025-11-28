from index.models import (
    Barcode,
    UserBarcodeSettings,
    UserBarcodePullSettings,
    BarcodeUsage,
)
from index.serializers import (
    BarcodeSerializer,
    BarcodeCreateSerializer,
    DynamicBarcodeWithProfileSerializer,
    UserBarcodeSettingsSerializer,
    UserBarcodePullSettingsSerializer,
)
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class BarcodeDashboardAPIView(APIView):
    """
    API endpoint for barcode dashboard functionality:
    - GET: Retrieve user settings and barcodes
    - POST: Update settings
    - PUT: Create new barcode
    - DELETE: Delete barcode

    Business rules:
    1. If user is in "User" group: associate_user_profile_with_barcode is
       permanently False and disabled
    2. When associate_user_profile_with_barcode is True, barcode field must be disabled and cleared  # noqa: E501
    3. Only DynamicBarcode and Others types can be managed
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user settings and barcodes"""
        user = request.user

        # Check if user is in User group - they shouldn't access this endpoint
        if user.groups.filter(name="User").exists():
            return Response(
                {"detail": "User type accounts cannot access barcode " "dashboard"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get or create user settings
        settings, created = UserBarcodeSettings.objects.get_or_create(
            user=user,
            defaults={
                "barcode": None,
                "associate_user_profile_with_barcode": False,
                "scanner_detection_enabled": False,
                "prefer_front_camera": True,
            },
        )

        # Force associate_user_profile_with_barcode to False for User group
        # members
        is_user_group = user.groups.filter(name="User").exists()
        if is_user_group and settings.associate_user_profile_with_barcode:
            settings.associate_user_profile_with_barcode = False
            settings.save()

        # Get barcodes based on user type
        is_school_group = user.groups.filter(name="School").exists()

        if is_school_group:
            # School users see:
            # - Dynamic barcodes that are shared by others OR owned by themselves  # noqa: E501
            # - Their own Identification and Others barcodes
            from django.db.models import Q

            barcodes = (
                Barcode.objects.filter(
                    (
                        Q(barcode_type="DynamicBarcode")
                        & (Q(user=user) | Q(share_with_others=True))
                    )
                    | Q(
                        user=user,
                        barcode_type__in=["Others", "Identification"],
                    )
                )
                .select_related("user")
                .prefetch_related("barcodeuserprofile", "barcodeusage_set")
                .order_by("-time_created")
            )
        else:
            # Other users see all of their own barcodes, including
            # Identification
            barcodes = (
                Barcode.objects.filter(
                    user=user,
                    barcode_type__in=[
                        "DynamicBarcode",
                        "Others",
                        "Identification",
                    ],
                )
                .select_related("user")
                .prefetch_related("barcodeuserprofile", "barcodeusage_set")
                .order_by("-time_created")
            )

        # Get or create pull settings
        pull_settings, _ = UserBarcodePullSettings.objects.get_or_create(
            user=user,
            defaults={"pull_setting": "Disable", "gender_setting": "Unknow"},
        )

        # Serialize data
        settings_serializer = UserBarcodeSettingsSerializer(
            settings, context={"request": request}
        )
        pull_settings_serializer = UserBarcodePullSettingsSerializer(pull_settings)
        barcodes_serializer = BarcodeSerializer(
            barcodes, many=True, context={"request": request}
        )

        return Response(
            {
                "settings": settings_serializer.data,
                "pull_settings": pull_settings_serializer.data,
                "barcodes": barcodes_serializer.data,
                "is_user_group": is_user_group,
                "is_school_group": user.groups.filter(name="School").exists(),
            }
        )

    def post(self, request):
        """Update user barcode settings and/or pull settings"""
        user = request.user

        # Check if user is in User group - they shouldn't access this endpoint
        if user.groups.filter(name="User").exists():
            return Response(
                {"detail": "User type accounts cannot access barcode " "dashboard"},
                status=status.HTTP_403_FORBIDDEN,
            )
        settings, _ = UserBarcodeSettings.objects.get_or_create(user=user)

        # Create a copy of request data to potentially modify
        data = request.data.copy()
        barcode_requested = "barcode" in data

        # Track pull setting state changes
        existing_pull_settings = UserBarcodePullSettings.objects.filter(
            user=user
        ).first()
        pull_settings_enabled_before = (
            existing_pull_settings.pull_setting == "Enable"
            if existing_pull_settings
            else False
        )
        pull_settings_enabled_after = pull_settings_enabled_before

        # Handle pull_settings if provided
        pull_settings_data = data.pop("pull_settings", None)
        if pull_settings_data:
            pull_settings, _ = UserBarcodePullSettings.objects.get_or_create(user=user)
            pull_serializer = UserBarcodePullSettingsSerializer(
                pull_settings, data=pull_settings_data, partial=True
            )
            if pull_serializer.is_valid():
                pull_serializer.save()
                pull_settings.refresh_from_db()
                pull_settings_enabled_after = pull_settings.pull_setting == "Enable"
            else:
                return Response(
                    {
                        "status": "error",
                        "errors": {"pull_settings": pull_serializer.errors},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            pull_settings = existing_pull_settings

        pull_setting_enabled_now = (
            pull_settings_data is not None
            and pull_settings_enabled_after
            and not pull_settings_enabled_before
        )

        if (
            barcode_requested
            and pull_settings_enabled_after
            and not pull_setting_enabled_now
        ):
            return Response(
                {
                    "status": "error",
                    "errors": {
                        "barcode": [
                            "Barcode selection is disabled when pull setting "
                            "is enabled."
                        ]
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # If pull_setting is enabled, auto-clear barcode selection
        if pull_settings_enabled_after:
            data.pop("barcode", None)  # Remove from incoming data
            if settings.barcode is not None:
                settings.barcode = None
                settings.save()

        # Let the serializer handle automatic setting of associate_user_profile_with_barcode  # noqa: E501
        # based on barcode type. No manual intervention needed here.

        serializer = UserBarcodeSettingsSerializer(
            settings, data=data, context={"request": request}, partial=True
        )

        if serializer.is_valid():
            serializer.save()

            # Get updated pull settings for response
            pull_settings, _ = UserBarcodePullSettings.objects.get_or_create(user=user)
            pull_settings_serializer = UserBarcodePullSettingsSerializer(pull_settings)

            return Response(
                {
                    "status": "success",
                    "message": "Barcode settings updated successfully",
                    "settings": serializer.data,
                    "pull_settings": pull_settings_serializer.data,
                }
            )

        return Response(
            {"status": "error", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def put(self, request):
        """Create new barcode"""
        # Check if user is in User group - they shouldn't access this endpoint
        if request.user.groups.filter(name="User").exists():
            return Response(
                {"detail": "User type accounts cannot access barcode " "dashboard"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = BarcodeCreateSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            barcode = serializer.save()
            # Record a transaction for barcode creation via service layer
            from index.services.transactions import TransactionService

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
        """Update properties of a barcode owned by the current user (share flag and daily limit)"""  # noqa: E501
        # Check if user is in User group - they shouldn't access this endpoint
        if request.user.groups.filter(name="User").exists():
            return Response(
                {"detail": "User type accounts cannot access barcode " "dashboard"},
                status=status.HTTP_403_FORBIDDEN,
            )

        barcode_id = request.data.get("barcode_id")
        share_with_others = request.data.get("share_with_others")
        daily_usage_limit = request.data.get("daily_usage_limit")

        if not barcode_id:
            return Response(
                {"status": "error", "message": "barcode_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            barcode = Barcode.objects.get(pk=barcode_id, user=request.user)
        except Barcode.DoesNotExist:
            return Response(
                {
                    "status": "error",
                    "message": "Barcode not found or you do not have "
                    "permission to update it",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Identification barcodes cannot be updated
        if barcode.barcode_type == "Identification":
            return Response(
                {
                    "status": "error",
                    "message": "Identification barcodes cannot be modified",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update share_with_others if provided
        if share_with_others is not None:
            # Coerce to boolean if sent as string
            if isinstance(share_with_others, str):
                share_with_others = share_with_others.lower() in [
                    "1",
                    "true",
                    "yes",
                    "on",
                ]
            barcode.share_with_others = bool(share_with_others)
            barcode.save()

        # Update daily_usage_limit if provided
        if daily_usage_limit is not None:
            try:
                # Ensure it's a non-negative integer
                limit_value = int(daily_usage_limit)
                if limit_value < 0:
                    return Response(
                        {
                            "status": "error",
                            "message": "Daily usage limit must be 0 or " "greater",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Get or create BarcodeUsage record
                usage, _ = BarcodeUsage.objects.get_or_create(
                    barcode=barcode, defaults={"total_usage": 0}
                )
                usage.daily_usage_limit = limit_value
                usage.save()
            except (ValueError, TypeError):
                return Response(
                    {
                        "status": "error",
                        "message": "Daily usage limit must be a valid number",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
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
        """
        Delete barcode - users may delete only their own barcodes
        (DynamicBarcode and Others types)
        """
        # Check if user is in User group - they shouldn't access this endpoint
        if request.user.groups.filter(name="User").exists():
            return Response(
                {"detail": "User type accounts cannot access barcode " "dashboard"},
                status=status.HTTP_403_FORBIDDEN,
            )

        barcode_id = request.data.get("barcode_id")

        if not barcode_id:
            return Response(
                {"status": "error", "message": "Barcode ID is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # All users can only delete barcodes they own
        try:
            barcode = Barcode.objects.get(
                pk=barcode_id,
                user=request.user,
                barcode_type__in=["DynamicBarcode", "Others"],
            )
        except Barcode.DoesNotExist:
            return Response(
                {
                    "status": "error",
                    "message": "Barcode not found or you do not have "
                    "permission to delete it",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if this barcode is currently selected in settings
        settings = UserBarcodeSettings.objects.filter(
            user=request.user, barcode=barcode
        ).first()

        if settings:
            settings.barcode = None
            settings.save()

        barcode.delete()

        return Response(
            {"status": "success", "message": "Barcode deleted successfully"}
        )


class DynamicBarcodeCreateAPIView(APIView):
    """
    API endpoint for creating dynamic barcodes with profile information.
    Only School group users can use this endpoint.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Create a new dynamic barcode with profile data"""
        # Check if user is in School group
        if not request.user.groups.filter(name="School").exists():
            return Response(
                {
                    "status": "error",
                    "message": "Only School group users can create dynamic barcodes",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = DynamicBarcodeWithProfileSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            barcode = serializer.save()
            # Record a transaction for barcode creation
            from index.services.transactions import TransactionService

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
            {"status": "error", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
