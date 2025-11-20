from io import BytesIO

from PIL import Image
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..helpers import _b64_any_to_bytes, _clean_base64


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_info(request):
    groups = list(request.user.groups.values_list("name", flat=True))
    try:
        profile = request.user.userprofile
        profile_data = {
            "name": profile.name,
            "information_id": profile.information_id,
        }
    except Exception:
        profile_data = None
    return Response(
        {
            "username": request.user.username,
            "groups": groups,
            "profile": profile_data,
        }
    )


@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def api_profile(request):
    try:
        profile = request.user.userprofile
    except Exception:
        return Response(
            {"success": False, "message": "Profile not found"}, status=404
        )

    if request.method == "GET":
        return Response(
            {
                "success": True,
                "data": {
                    "name": profile.name,
                    "information_id": profile.information_id,
                    "has_passkey": hasattr(request.user, "passkey"),
                },
            }
        )

    data = request.data
    errors = {}
    if "name" in data and not data["name"].strip():
        errors["name"] = "Name cannot be empty"
    if "information_id" in data and not data["information_id"].strip():
        errors["information_id"] = "Information ID cannot be empty"

    if errors:
        return Response({"success": False, "errors": errors}, status=400)

    if "name" in data:
        profile.name = data["name"]
    if "information_id" in data:
        profile.information_id = data["information_id"]
    if "user_profile_img_base64" in data:
        b64 = _clean_base64(data["user_profile_img_base64"])
        if b64:
            try:
                img_bytes = _b64_any_to_bytes(b64)
                try:
                    with Image.open(BytesIO(img_bytes)) as _:
                        pass
                except Exception:
                    raise ValueError("Not a valid image format")
                profile.user_profile_img = b64
            except Exception:
                return Response(
                    {
                        "success": False,
                        "errors": {
                            "user_profile_img": "Invalid Base64 avatar data"
                        },
                    },
                    status=400,
                )
        else:
            profile.user_profile_img = None

    profile.save()
    return Response(
        {"success": True, "message": "Profile updated successfully"}
    )
