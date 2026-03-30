import logging
from io import BytesIO

from PIL import Image
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..forms import UserRegisterForm

MAX_AVATAR_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
from ..helpers import _b64_any_to_bytes


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_img(request):
    profile = getattr(request.user, "userprofile", None)
    if not profile or not profile.user_profile_img:
        return HttpResponse(status=404)

    b64 = profile.user_profile_img
    if b64.startswith("data:image"):
        b64 = b64.split(",", 1)[1]

    try:
        img_bytes = _b64_any_to_bytes(b64)
    except (ValueError, OSError):
        return HttpResponse(status=400)

    try:
        with Image.open(BytesIO(img_bytes)) as img:
            fmt = img.format
            mime = Image.MIME.get(fmt)
    except (ValueError, IOError, OSError):
        return HttpResponse(status=400)
    if not mime:
        return HttpResponse(status=400)

    response = HttpResponse(img_bytes, content_type=mime)
    response["Cache-Control"] = "private, max-age=3600"
    return response


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_avatar_upload(request):
    try:
        profile = request.user.userprofile
    except ObjectDoesNotExist:
        return Response({"success": False, "message": "Profile not found"}, status=404)

    if "avatar" not in request.FILES:
        return Response(
            {"success": False, "message": "No avatar file provided"},
            status=400,
        )

    avatar_file = request.FILES["avatar"]

    if not avatar_file.content_type.startswith("image/"):
        return Response({"success": False, "message": "Invalid file type"}, status=400)

    ALLOWED_SIGNATURES = [b"\xff\xd8\xff", b"\x89PNG", b"GIF87a", b"GIF89a"]
    header = avatar_file.read(8)
    avatar_file.seek(0)
    if not any(header.startswith(sig) for sig in ALLOWED_SIGNATURES):
        return Response({"success": False, "message": "Invalid image file"}, status=400)

    if avatar_file.size > MAX_AVATAR_SIZE_BYTES:
        max_mb = MAX_AVATAR_SIZE_BYTES // (1024 * 1024)
        return Response(
            {"success": False, "message": f"File size must be less than {max_mb}MB"},
            status=400,
        )

    try:
        form = UserRegisterForm()
        with Image.open(avatar_file) as im:
            b64 = form._pil_to_base64(im)

        profile.user_profile_img = b64
        profile.save()

        return Response({"success": True, "message": "Avatar uploaded successfully"})
    except (ValueError, IOError, OSError):
        logging.exception("Error processing avatar image upload")
        return Response(
            {"success": False, "message": "Failed to process image."},
            status=500,
        )
