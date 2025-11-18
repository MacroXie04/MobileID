import base64
import io
from dataclasses import dataclass
from typing import Optional

from PIL import Image
from django.contrib.auth.models import User
from django.db import transaction
from index.models import (
    Barcode,
    BarcodeUserProfile,
    UserBarcodeSettings,
)
from index.project_code.dynamic_barcode import ApiResponse
from index.services.transactions import TransactionService

from .dynamic_barcode import UCMercedMobileIdClient


@dataclass
class BarcodeData:
    barcode: str
    user_profile_img: str
    username: str
    information_id: str
    user_cookies: str

    def to_dict(self) -> dict:
        return {
            "barcode": self.barcode,
            "user_profile_img": self.user_profile_img,
            "username": self.username,
            "information_id": self.information_id,
            "user_cookies": self.user_cookies,
        }


class TransferBarcode(UCMercedMobileIdClient):
    def __init__(
            self, user_cookies: str, user: Optional[User] = None, headless: bool = True
    ):
        super().__init__(headless=headless)
        self.barcode_user: Optional[User] = user
        self.user_cookies: str = user_cookies

    def process_barcode_data(self) -> BarcodeData:
        mobile_data = self.get_mobile_id_data(self.user_cookies)
        converted_png_b64 = self._convert_profile_image_to_png_128(
            mobile_data.profile_img_base64 or ""
        )

        # Validate that we have meaningful data before proceeding
        if not self._has_meaningful_data(mobile_data):
            raise ValueError(
                "No meaningful mobile ID data found. Please check your credentials and try again."
            )

        return BarcodeData(
            barcode=mobile_data.barcode or "",
            user_profile_img=converted_png_b64,
            username=mobile_data.username or "",
            information_id=mobile_data.student_id or "",
            user_cookies=self.user_cookies,
        )

    def store_barcode_data(self, barcode_data: BarcodeData) -> None:
        # store the barcode data in the database
        if not self.barcode_user:
            raise ValueError("Target user is required to store barcode data.")

        user = self.barcode_user
        raw_barcode = (barcode_data.barcode or "").strip()
        if not raw_barcode:
            raise ValueError("No barcode value provided.")

        # All transferred barcodes are set as DynamicBarcode type
        barcode_type = "DynamicBarcode"
        is_digits = raw_barcode.isdigit()

        # Normalize value for DynamicBarcode storage
        if is_digits and len(raw_barcode) == 28:
            # For 28-digit barcodes, store only the last 14 digits as dynamic base
            normalized_value = raw_barcode[-14:]
        elif is_digits and len(raw_barcode) >= 14:
            # For other long digit sequences, take the last 14 digits
            normalized_value = raw_barcode[-14:]
        else:
            # For shorter barcodes or non-digit sequences, truncate to 120 chars max
            # but still treat as DynamicBarcode
            normalized_value = raw_barcode[:120]

        with transaction.atomic():
            # Upsert the Barcode for this user
            existing = Barcode.objects.filter(barcode=normalized_value).first()
            if existing:
                if existing.user_id != user.id:
                    raise ValueError("Barcode already exists for a different user.")
                if existing.barcode_type != barcode_type:
                    existing.barcode_type = barcode_type
                    existing.save(update_fields=["barcode_type"])
                barcode_obj = existing
            else:
                barcode_obj = Barcode.objects.create(
                    user=user,
                    barcode=normalized_value,
                    barcode_type=barcode_type,
                )
                # Record transaction for new barcode creation
                TransactionService.create_transaction(
                    user=user,
                    barcode=barcode_obj,
                )

            # Upsert BarcodeUserProfile (OneToOne)
            name = (barcode_data.username or "").strip() or user.username
            information_id = (barcode_data.information_id or "").strip()
            # Store the full base64 PNG (already normalized to 128x128)
            # Do not truncate, otherwise the image becomes corrupted/half-rendered
            avatar_b64 = (barcode_data.user_profile_img or "").strip() or None
            cookies = (barcode_data.user_cookies or "").strip() or None

            try:
                profile = barcode_obj.barcodeuserprofile
                updates = []
                if profile.name != name:
                    profile.name = name
                    updates.append("name")
                if information_id and profile.information_id != information_id:
                    profile.information_id = information_id
                    updates.append("information_id")
                if avatar_b64 is not None and profile.user_profile_img != avatar_b64:
                    profile.user_profile_img = avatar_b64
                    updates.append("user_profile_img")
                if cookies is not None and profile.user_cookies != cookies:
                    profile.user_cookies = cookies
                    updates.append("user_cookies")
                if updates:
                    profile.save(update_fields=updates)
            except BarcodeUserProfile.DoesNotExist:
                BarcodeUserProfile.objects.create(
                    linked_barcode=barcode_obj,
                    name=name,
                    information_id=information_id,
                    user_profile_img=avatar_b64,
                    user_cookies=cookies,
                )

            # Ensure user's settings point to this barcode
            settings, _ = UserBarcodeSettings.objects.get_or_create(user=user)
            changed = False
            if settings.barcode_id != barcode_obj.id:
                settings.barcode = barcode_obj
                changed = True
            # For transferred barcodes, enable profile association by default
            if not settings.associate_user_profile_with_barcode:
                settings.associate_user_profile_with_barcode = True
                changed = True
            if changed:
                settings.save()

    def _has_meaningful_data(self, mobile_data) -> bool:
        """
        Check if the mobile data contains meaningful information.
        Returns True if at least some key data is present, False otherwise.
        """
        # Check for essential data - we need at least some of these to be meaningful
        has_barcode = bool(mobile_data.barcode and mobile_data.barcode.strip())
        has_student_id = bool(mobile_data.student_id and mobile_data.student_id.strip())
        has_mobile_codes = bool(
            mobile_data.mobile_id_rand_array
            and len(mobile_data.mobile_id_rand_array) > 0
        )

        # Username validation - check if it's not just generic text
        has_meaningful_username = False
        if mobile_data.username and mobile_data.username.strip():
            username = mobile_data.username.strip()
            # Check if username is not just generic institutional text
            generic_texts = [
                "university of california",
                "uc merced",
                "merced",
                "university",
                "college",
                "institution",
                "campus",
            ]
            username_lower = username.lower()
            has_meaningful_username = not any(
                generic in username_lower for generic in generic_texts
            )

        # We need at least 2 out of 4 meaningful pieces of data
        meaningful_count = sum(
            [has_barcode, has_student_id, has_mobile_codes, has_meaningful_username]
        )

        return meaningful_count >= 2

    def _convert_profile_image_to_png_128(self, possibly_data_uri_b64: str) -> str:
        try:
            if not possibly_data_uri_b64:
                return ""

            # Strip data URI prefix if present
            if "," in possibly_data_uri_b64 and possibly_data_uri_b64.startswith(
                    "data:image"
            ):
                _, b64_data = possibly_data_uri_b64.split(",", 1)
            else:
                b64_data = possibly_data_uri_b64

            raw_bytes = base64.b64decode(b64_data, validate=False)
            with Image.open(io.BytesIO(raw_bytes)) as img:
                # Convert to RGB if needed
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGB")

                # Center-crop to square
                width, height = img.size
                if width != height:
                    min_side = min(width, height)
                    left = (width - min_side) // 2
                    top = (height - min_side) // 2
                    right = left + min_side
                    bottom = top + min_side
                    img = img.crop((left, top, right, bottom))

                # Resize to 128x128
                img = img.resize((128, 128), Image.LANCZOS)

                # Save as PNG to memory
                output = io.BytesIO()
                img.save(output, format="PNG")
                png_bytes = output.getvalue()
                return base64.b64encode(png_bytes).decode("ascii")
        except Exception:
            # On any failure, return empty to avoid storing invalid data
            return ""

    def transfer_barcode(self) -> ApiResponse:
        try:
            barcode_data = self.process_barcode_data()
            self.store_barcode_data(barcode_data)
            return ApiResponse(
                status="success", response="Stored to BarcodeUserProfile"
            )
        except ValueError as ve:
            # Handle validation errors (no meaningful data)
            return ApiResponse(status="error", error=str(ve))
        except Exception as exc:
            return ApiResponse(status="error", error=str(exc))
