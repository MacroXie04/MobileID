from index.services.barcode import generate_barcode
from index.models import UserBarcodeSettings, BarcodeUserProfile
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
import base64


class ActiveProfileAPIView(APIView):
    """Get the active profile info based on user settings"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"ActiveProfileAPIView called by user: {request.user.username}")
        
        # Check if user is School type
        if not request.user.groups.filter(name="School").exists():
            logger.info(f"User {request.user.username} is not School type")
            return Response({'profile_info': None})
        
        try:
            settings = UserBarcodeSettings.objects.get(user=request.user)
            logger.info(f"User settings found: associate_user_profile_with_barcode={settings.associate_user_profile_with_barcode}, barcode={settings.barcode}")
            
            if settings.associate_user_profile_with_barcode and settings.barcode:
                try:
                    barcode_profile = settings.barcode.barcodeuserprofile
                    logger.info(f"BarcodeUserProfile found: {barcode_profile.name}")
                    
                    profile_data = {
                        'name': barcode_profile.name,
                        'information_id': barcode_profile.information_id,
                        'has_avatar': bool(barcode_profile.user_profile_img),
                    }
                    # Add avatar data if exists
                    if barcode_profile.user_profile_img:
                        img_data = barcode_profile.user_profile_img
                        if not img_data.startswith('data:image'):
                            # Default to PNG format
                            img_data = f'data:image/png;base64,{img_data}'
                        profile_data['avatar_data'] = img_data
                    
                    logger.info(f"Returning profile data for: {profile_data['name']}")
                    return Response({'profile_info': profile_data})
                except BarcodeUserProfile.DoesNotExist:
                    logger.info("BarcodeUserProfile does not exist for selected barcode")
                    pass
        except UserBarcodeSettings.DoesNotExist:
            logger.info("UserBarcodeSettings does not exist")
            pass
        
        logger.info("Returning None for profile_info")
        return Response({'profile_info': None})


class GenerateBarcodeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        result = generate_barcode(request.user)
        
        # If barcode generation was successful and user is School type
        if result.get('status') == 'success' and request.user.groups.filter(name="School").exists():
            # Check if user has settings and associate_user_profile_with_barcode is true
            try:
                settings = UserBarcodeSettings.objects.get(user=request.user)
                if settings.associate_user_profile_with_barcode and settings.barcode:
                    # Check if the selected barcode has a profile
                    try:
                        barcode_profile = settings.barcode.barcodeuserprofile
                        # Add barcode profile info to result
                        result['profile_info'] = {
                            'name': barcode_profile.name,
                            'information_id': barcode_profile.information_id,
                            'has_avatar': bool(barcode_profile.user_profile_img),
                        }
                        # Add avatar data if exists
                        if barcode_profile.user_profile_img:
                            img_data = barcode_profile.user_profile_img
                            # Ensure it has proper data URI format
                            if not img_data.startswith('data:image'):
                                # Try to detect image type from base64 data
                                try:
                                    img_bytes = base64.b64decode(img_data[:100])  # Check first 100 chars
                                    if img_bytes.startswith(b'\xff\xd8'):
                                        img_data = f'data:image/jpeg;base64,{img_data}'
                                    elif img_bytes.startswith(b'\x89PNG'):
                                        img_data = f'data:image/png;base64,{img_data}'
                                    else:
                                        img_data = f'data:image/png;base64,{img_data}'  # Default to PNG
                                except:
                                    img_data = f'data:image/png;base64,{img_data}'  # Default to PNG
                            result['profile_info']['avatar_data'] = img_data
                    except BarcodeUserProfile.DoesNotExist:
                        pass
            except UserBarcodeSettings.DoesNotExist:
                pass
        
        return Response(result, status=200)
