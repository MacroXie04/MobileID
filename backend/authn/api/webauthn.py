# authn/views.py
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

class CookieTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            access, refresh = response.data["access"], response.data["refresh"]
            response.set_cookie("access_token", access, httponly=True,
                                samesite="Lax", secure=False, max_age=1800)
            response.set_cookie("refresh_token", refresh, httponly=True,
                                samesite="Lax", secure=False, max_age=7*24*3600)
            response.data = {"message": "Login successful"}
        return response

@api_view(["POST"])
def api_logout(request):
    resp = Response({"message": "Logged out"})
    resp.delete_cookie("access_token")
    resp.delete_cookie("refresh_token")
    return resp

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_info(request):
    groups = list(request.user.groups.values_list("name", flat=True))
    try:
        profile = request.user.userprofile
        profile_data = {
            "name": profile.name,
            "information_id": profile.information_id,
            "user_profile_img": profile.user_profile_img,
        }
    except Exception:
        profile_data = None
    return Response({"username": request.user.username,
                     "groups": groups,
                     "profile": profile_data})
