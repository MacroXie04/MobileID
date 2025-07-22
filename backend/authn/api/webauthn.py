# authn/views.py
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny

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
            "user_profile_img": profile.user_profile_img,
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
    from django.contrib.auth import login
    from authn.forms.WebAuthnForms import UserRegisterForm
    from rest_framework.throttling import AnonRateThrottle
    from rest_framework.decorators import throttle_classes
    
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
                max_age=1800  # 30 minutes
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



