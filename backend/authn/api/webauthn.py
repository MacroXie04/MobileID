# authn/views.py
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import login
from rest_framework.throttling import AnonRateThrottle
from rest_framework.decorators import throttle_classes
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from PIL import Image
import base64
from io import BytesIO
from authn.services.webauthn import create_user_profile


class UserRegisterForm(UserCreationForm):
    # Extra visible fields
    name = forms.CharField(max_length=100, label="Name")
    information_id = forms.CharField(max_length=100, label="Information ID")

    # Raw file input (hidden by CSS – selection handled via JS)
    user_profile_img = forms.ImageField(required=False, label="")

    # Base64 string produced by Cropper.js
    user_profile_img_base64 = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        label="",
    )

    class Meta:
        model = User
        fields = (
            "username",
            "password1",
            "password2",
            "name",
            "information_id",
            "user_profile_img",
            "user_profile_img_base64",
        )

    # ---------- validation helpers ---------- #
    def clean(self):
        data = super().clean()
        # Avatar is optional - no validation required
        return data

    @staticmethod
    def _pil_to_base64(pil_img: Image.Image) -> str:
        """Center-crop, resize → 128×128 PNG → Base64 (no data URI)."""
        min_side = min(pil_img.size)
        left = (pil_img.width - min_side) // 2
        top = (pil_img.height - min_side) // 2
        pil_img = pil_img.crop((left, top, left + min_side, top + min_side))
        pil_img = pil_img.resize((128, 128), Image.LANCZOS)

        buf = BytesIO()
        pil_img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    # ---------- persistence ---------- #
    def save(self, commit=True):
        user = super().save(commit)
        name = self.cleaned_data["name"]
        info_id = self.cleaned_data["information_id"]

        # Determine avatar data - prefer client-cropped Base64, else process raw file, else use default
        avatar_b64 = ""
        if self.cleaned_data.get("user_profile_img_base64"):
            avatar_b64 = self.cleaned_data["user_profile_img_base64"]
        elif self.cleaned_data.get("user_profile_img"):
            with Image.open(self.cleaned_data["user_profile_img"]) as im:
                avatar_b64 = self._pil_to_base64(im)
        # If no avatar provided, avatar_b64 remains empty string

        create_user_profile(user, name, info_id, avatar_b64)
        return user

class CookieTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]
    
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
            # user_profile_img removed from here - now available at separate endpoint
        }
    except Exception:
        profile_data = None
    return Response({"username": request.user.username,
                     "groups": groups,
                     "profile": profile_data})


@api_view(["POST"])
@permission_classes([AllowAny])
def api_register(request):
    """
    register a new user
    """
    
    # apply registration rate limit
    class RegisterThrottle(AnonRateThrottle):
        scope = 'registration'
    
    # manually check rate limit
    throttle = RegisterThrottle()
    if not throttle.allow_request(request, None):
        return Response({
            'success': False,
            'message': 'Registration request is too frequent, please try again later'
        }, status=429)
    
    try:
        # validate required fields
        required_fields = ['username', 'password1', 'password2', 'name', 'information_id']
        missing_fields = []
        for field in required_fields:
            if not request.data.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            return Response({
                'success': False,
                'message': 'Missing required fields',
                'errors': {field: ['This field cannot be empty'] for field in missing_fields}
            }, status=400)
        
        # prepare form data
        form_data = {
            'username': request.data.get('username'),
            'password1': request.data.get('password1'),
            'password2': request.data.get('password2'),
            'name': request.data.get('name'),
            'information_id': request.data.get('information_id'),
            'user_profile_img_base64': request.data.get('user_profile_img_base64', ''),
        }
        
        # create form instance for validation
        form = UserRegisterForm(data=form_data)
        
        if form.is_valid():
            # save user
            user = form.save()
            
            # login user
            login(request, user)
            
            # set JWT cookies
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            
            response = Response({
                'success': True,
                'message': 'Registration successful',
                'data': {
                    'username': user.username,
                    'groups': list(user.groups.values_list('name', flat=True)),
                }
            })
            
            # set JWT cookies
            response.set_cookie(
                "access_token", 
                access_token, 
                httponly=True,
                samesite="Lax", 
                secure=False, 
                max_age=1800
            )
            response.set_cookie(
                "refresh_token", 
                refresh_token, 
                httponly=True,
                samesite="Lax", 
                secure=False, 
                max_age=7*24*3600  # 7 days
            )
            
            return response
            
        else:
            # form validation failed, return error message
            errors = {}
            for field, field_errors in form.errors.items():
                if field == '__all__':
                    errors['general'] = field_errors
                else:
                    errors[field] = field_errors
            
            return Response({
                'success': False,
                'message': 'Registration information validation failed',
                'errors': errors
            }, status=400)
            
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Registration failed: {str(e)}'
        }, status=500)