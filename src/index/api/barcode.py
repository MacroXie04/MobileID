import logging

from index.repositories import BarcodeRepository, SettingsRepository
from index.services.barcode import generate_barcode
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class ActiveProfileAPIView(APIView):
    """Get the active profile info based on user settings"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        logger.info("ActiveProfileAPIView called by user: %s", request.user.username)

        settings = SettingsRepository.get(request.user.id)
        if not settings:
            logger.info("UserBarcodeSettings does not exist")
            logger.info("Returning None for profile_info")
            return Response({"profile_info": None})

        logger.info(
            "User settings found: associate_user_profile_with_barcode=%s, "
            "barcode=%s",
            settings.get("associate_user_profile_with_barcode"),
            settings.get("active_barcode_uuid"),
        )

        active_uuid = settings.get("active_barcode_uuid")
        if settings.get("associate_user_profile_with_barcode") and active_uuid:
            barcode = BarcodeRepository.get_by_uuid(request.user.id, active_uuid)
            if not barcode:
                # Could be a shared barcode from another user
                shared = BarcodeRepository.get_shared_dynamic_barcodes()
                barcode = next(
                    (b for b in shared if b["barcode_uuid"] == active_uuid), None
                )

            if barcode and barcode.get("profile_name"):
                logger.info("BarcodeUserProfile found: %s", barcode.get("profile_name"))

                profile_data = {
                    "name": barcode.get("profile_name"),
                    "information_id": barcode.get("profile_info_id"),
                    "has_avatar": bool(barcode.get("profile_avatar")),
                }
                # Add avatar data if exists
                if barcode.get("profile_avatar"):
                    img_data = barcode["profile_avatar"]
                    if not img_data.startswith("data:image"):
                        img_data = f"data:image/png;base64,{img_data}"
                    profile_data["avatar_data"] = img_data

                logger.info("Returning profile data for: %s", profile_data["name"])
                return Response({"profile_info": profile_data})
            else:
                logger.info("BarcodeUserProfile does not exist for selected barcode")

        logger.info("Returning None for profile_info")
        return Response({"profile_info": None})


class GenerateBarcodeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        result = generate_barcode(request.user)
        return Response(result, status=200)
