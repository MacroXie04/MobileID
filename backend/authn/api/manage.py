import base64
from io import BytesIO

from PIL import Image
from django.http import HttpResponse
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from authn.models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """user info serializer"""
    user_profile_img = serializers.CharField(required=False, allow_blank=True, help_text="Base64编码的头像图片")
    
    class Meta:
        model = UserProfile
        fields = ['name', 'information_id', 'user_profile_img']
        
    def validate_user_profile_img(self, value):
        """validate avatar data"""
        if not value:
            return value
            
        try:
            # try to decode base64 data
            image_data = base64.b64decode(value)
            # validate if it is a valid image
            with Image.open(BytesIO(image_data)) as img:
                # check image format
                if img.format not in ['PNG', 'JPEG', 'JPG']:
                    raise serializers.ValidationError("User avatar must be PNG or JPEG format")
                # check image size (optional)
                if img.size[0] > 1024 or img.size[1] > 1024:
                    raise serializers.ValidationError("User avatar size must be less than 1024x1024 pixels")
        except Exception as e:
            raise serializers.ValidationError(f"User avatar data is invalid: {str(e)}") # avatar data is invalid
            
        return value
    
    def validate_name(self, value):
        """validate name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        if len(value.strip()) > 100:
            raise serializers.ValidationError("Name length cannot be more than 100 characters")
        return value.strip()
    
    def validate_information_id(self, value):
        """validate information ID"""
        if not value or not value.strip():
            raise serializers.ValidationError("Information ID cannot be empty")
        if len(value.strip()) > 100:
            raise serializers.ValidationError("Information ID length cannot be more than 100 characters")
        return value.strip()

    def _process_avatar_image(self, base64_str):
        """process avatar image: resize to 128x128 and convert to PNG format"""
        try:
            # decode base64 data
            image_data = base64.b64decode(base64_str)
            
            # open image
            with Image.open(BytesIO(image_data)) as img:
                # convert to RGB mode (optional)
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # crop to square
                min_side = min(img.size)
                x0 = (img.width - min_side) // 2
                y0 = (img.height - min_side) // 2
                img = img.crop((x0, y0, x0 + min_side, y0 + min_side))
                
                # resize to 128x128
                img = img.resize((128, 128), Image.LANCZOS)
                
                # save as PNG format base64
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                return base64.b64encode(buffer.getvalue()).decode()
                
        except Exception as e:
            raise serializers.ValidationError(f"User avatar processing failed: {str(e)}")
    
    def update(self, instance, validated_data):
        """update user info"""
        # process avatar
        avatar_data = validated_data.get('user_profile_img')
        if avatar_data:
            validated_data['user_profile_img'] = self._process_avatar_image(avatar_data)
        
        # update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class UserProfileThrottle(UserRateThrottle):
    """user info edit frequency limit"""
    scope = 'user_profile'


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserProfileThrottle])
def user_profile_api(request):
    """
    user info management API
    
    GET: get current user info
    PUT/PATCH: update user info (avatar, name, informationID)
    """
    try:
        # get or create user profile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        if request.method == 'GET':
            # return user info
            serializer = UserProfileSerializer(profile)
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'User info get success'
            })
        
        elif request.method in ['PUT', 'PATCH']:
            # update user info
            partial = request.method == 'PATCH'
            serializer = UserProfileSerializer(profile, data=request.data, partial=partial)
            
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'data': serializer.data,
                    'message': 'User info update success'
                })
            else:
                return Response({
                    'success': False,
                    'errors': serializer.errors,
                    'message': 'User info validation failed'
                }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Server error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserProfileThrottle])
def upload_avatar_api(request):
    """
    avatar upload API (support file upload)
    
    POST: upload avatar file, automatically process and update user avatar
    """
    try:
        # get or create user profile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        # check if there is a file to upload
        if 'avatar' not in request.FILES:
            return Response({
                'success': False,
                'message': 'Please select the avatar file to upload'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        avatar_file = request.FILES['avatar']
        
        # validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png']
        if avatar_file.content_type not in allowed_types:
            return Response({
                'success': False,
                'message': 'Avatar file must be JPEG or PNG format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # validate file size (5MB limit)
        if avatar_file.size > 5 * 1024 * 1024:
            return Response({
                'success': False,
                'message': 'Avatar file size cannot be more than 5MB'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # process image
            with Image.open(avatar_file) as img:
                # convert to RGB mode
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # crop to square
                min_side = min(img.size)
                x0 = (img.width - min_side) // 2
                y0 = (img.height - min_side) // 2
                img = img.crop((x0, y0, x0 + min_side, y0 + min_side))
                
                # resize to 128x128
                img = img.resize((128, 128), Image.LANCZOS)
                
                # save as PNG format base64
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                base64_avatar = base64.b64encode(buffer.getvalue()).decode()
                
                # update user avatar
                profile.user_profile_img = base64_avatar
                profile.save()
                
                return Response({
                    'success': True,
                    'data': {
                        'user_profile_img': base64_avatar
                    },
                    'message': 'Avatar upload success'
                })
                
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Avatar processing failed: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Server error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserProfileThrottle])
def get_avatar_api(request):
    """
    Get user avatar as image
    
    GET: returns user avatar as image/png response
    """
    try:
        # Get user profile
        try:
            profile = request.user.userprofile
        except UserProfile.DoesNotExist:
            # Return default avatar or 404
            return Response({
                'success': False,
                'message': 'User profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user has avatar
        if not profile.user_profile_img:
            # Return default avatar or 404
            return Response({
                'success': False,
                'message': 'No avatar uploaded'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # Remove data URL prefix if present
            image_data = profile.user_profile_img
            if image_data.startswith('data:image'):
                # Extract base64 data from data URL
                image_data = image_data.split(',')[1]
            
            # Decode base64 to bytes
            image_bytes = base64.b64decode(image_data)
            
            # Create HTTP response with image
            response = HttpResponse(image_bytes, content_type='image/png')
            response['Content-Disposition'] = f'inline; filename="avatar_{request.user.username}.png"'
            
            # Add cache headers to improve performance
            response['Cache-Control'] = 'private, max-age=3600'  # Cache for 1 hour
            
            return response
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Failed to decode avatar: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Server error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
