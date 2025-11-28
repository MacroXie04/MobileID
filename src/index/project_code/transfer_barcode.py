import base64
import io
from dataclasses import dataclass
from typing import Optional

from PIL import Image
from django.conf import settings
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
        self,
        user_cookies: str,
        user: Optional[User] = None,
        headless: bool = True,
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
                "No meaningful mobile ID data found. Please check your credentials and try again."  # noqa: E501
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
            # For 28-digit barcodes, store only the last 14 digits as dynamic base  # noqa: E501
            normalized_value = raw_barcode[-14:]
        elif is_digits and len(raw_barcode) >= 14:
            # For other long digit sequences, take the last 14 digits
            normalized_value = raw_barcode[-14:]
        else:
            # For shorter barcodes or non-digit sequences, truncate to 120 chars max  # noqa: E501
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
            # Do not truncate, otherwise the image becomes corrupted/half-rendered  # noqa: E501
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
        # Check for essential data - we need at least some of these to be meaningful  # noqa: E501
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
            [
                has_barcode,
                has_student_id,
                has_mobile_codes,
                has_meaningful_username,
            ]
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
        if hasattr(settings, "SELENIUM_ENABLED") and not settings.SELENIUM_ENABLED:
            return ApiResponse(
                status="error", error="Selenium disabled on Google Cloud"
            )

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

if __name__ == "__main__":
    import os

    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    django.setup()

    transfer_barcode = TransferBarcode(
        user_cookies="_scid=njgcOEfixQa9v_yNlmcaS7NN2LiUwg2g; "
        "_tt_enable_cookie=1; _ttp=01K10A60004X4B79PVZSMB962Z_.tt.1; "
        "_fbp=fb.1.1753431080973.171835158316531023; "
        "_mkto_trk=id:976-RKA-196&token:_mch-ucmerced.edu-287fe55e56c57e83ed76955576ad8151; "
        "_ga_QHQ86LM5JZ=GS2.1.s1753680653$o2$g0$t1753680653$j60$l0$h0; "
        "nmstat=874ae77e-31c0-3db1-0a94-7e352a5a73c8; "
        "_ga_12VFZGH5J2=GS2.2.s1760393693$o1$g0$t1760393693$j60$l0$h0; "
        "_ga_M8M8RKSXXK=GS2.1.s1762323113$o4$g0$t1762323113$j60$l0$h0; "
        "_ga_MDV0RFSJ6H=GS2.1.s1762479374$o3$g0$t1762479374$j60$l0$h0; "
        "_ga_ZNSTZ2YGVJ=GS2.1.s1762988876$o2$g1$t1762988887$j49$l0$h0; "
        "_ScCbts=%5B%5D; "
        "_ga_8F7K2W04Y2=GS2.2.s1764063319$o4$g0$t1764063319$j60$l0$h0; "
        "ttcsid_CSFURPRC77UC379F8IVG=1764249423850::mf-iTklwdxU6pfbHa9Dw.3.1764249424445.0; "
        "_ga_TSE2LSBDQZ=GS2.1.s1764307058$o23$g0$t1764307058$j60$l0$h0; "
        "_ga=GA1.2.34565484.1753431075; _gid=GA1.2.1821820024.1764307058; "
        "_sctr=1%7C1764230400000; "
        "_scid_r=p7gcOEfixQa9v_yNlmcaS7NN2LiUwg2gUV8n5A; "
        "ttcsid=1764307058431::t1tczPKSAerSpDdxTUb2.55.1764307078944.0; "
        "ttcsid_C8LNTT0H473GVAFU5FV0=1764307058430::hPouyQ3y6UnhUHOU3UQ6.55.1764307078945.0; "
        "_uetsid=1f9d8e30c91d11f0a2a7c130af990b21; "
        "_uetvid=f2200fb0692e11f0b0554f688142cbe8; "
        "session_for%3Aindex_php=ST-1764334770489-0iMUoxsTYaLrsPSL591udl0BS; "
        "_pk_ref.1.cb1f=%5B%22%22%2C%22%22%2C1764334772%2C%22https%3A%2F%2Fapi-70cee857.duosecurity.com%2F%22%5D; "
        "_pk_id.1.cb1f=8fd908bc11af365d.1750952586.34.1764334772.1764334772.; "
        "_pk_ses.1.cb1f=*"
    )
    result = transfer_barcode.transfer_barcode()
    print(result)
