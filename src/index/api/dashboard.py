from index.models import Barcode, UserBarcodeSettings
from index.serializers import (
    BarcodeSerializer,
    BarcodeCreateSerializer,
    UserBarcodeSettingsSerializer
)
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class BarcodeDashboardAPIView(APIView):
    """
    API endpoint for barcode dashboard functionality:
    - GET: Retrieve user settings and barcodes
    - POST: Update settings
    - PUT: Create new barcode
    - DELETE: Delete barcode

    Business rules:
    1. If user is in "User" group: associate_user_profile_with_barcode is permanently False and disabled
    2. When associate_user_profile_with_barcode is True, barcode field must be disabled and cleared
    3. Only DynamicBarcode and Others types can be managed
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user settings and barcodes"""
        user = request.user
        
        # Check if user is in User group - they shouldn't access this endpoint
        if user.groups.filter(name="User").exists():
            return Response({
                'detail': 'User type accounts cannot access barcode dashboard'
            }, status=status.HTTP_403_FORBIDDEN)

        # Get or create user settings
        settings, created = UserBarcodeSettings.objects.get_or_create(
            user=user,
            defaults={
                'barcode': None,
                'server_verification': False,
                'associate_user_profile_with_barcode': False
            }
        )

        # Force associate_user_profile_with_barcode to False for User group members
        is_user_group = user.groups.filter(name="User").exists()
        if is_user_group and settings.associate_user_profile_with_barcode:
            settings.associate_user_profile_with_barcode = False
            settings.save()

        # Get barcodes based on user type
        is_school_group = user.groups.filter(name="School").exists()
        
        if is_school_group:
            # School users see all dynamic barcodes plus their own others
            from django.db.models import Q
            barcodes = (
                Barcode.objects.filter(
                    Q(barcode_type='DynamicBarcode') |  # All dynamic barcodes
                    Q(user=user, barcode_type='Others')  # Their own Others type
                )
                .select_related('user')
                .prefetch_related('barcodeuserprofile', 'barcodeusage_set')
                .order_by('-time_created')
            )
        else:
            # Other users only see their own non-identification barcodes
            barcodes = (
                Barcode.objects.filter(
                    user=user,
                    barcode_type__in=['DynamicBarcode', 'Others']
                )
                .select_related('user')
                .prefetch_related('barcodeuserprofile', 'barcodeusage_set')
                .order_by('-time_created')
            )

        # Serialize data
        settings_serializer = UserBarcodeSettingsSerializer(
            settings,
            context={'request': request}
        )
        barcodes_serializer = BarcodeSerializer(barcodes, many=True, context={'request': request})

        return Response({
            'settings': settings_serializer.data,
            'barcodes': barcodes_serializer.data,
            'is_user_group': is_user_group,
            'is_school_group': user.groups.filter(name="School").exists()
        })

    def post(self, request):
        """Update user barcode settings"""
        user = request.user
        
        # Check if user is in User group - they shouldn't access this endpoint
        if user.groups.filter(name="User").exists():
            return Response({
                'detail': 'User type accounts cannot access barcode dashboard'
            }, status=status.HTTP_403_FORBIDDEN)
        settings, _ = UserBarcodeSettings.objects.get_or_create(user=user)

        # Create a copy of request data to potentially modify
        data = request.data.copy()

        # Let the serializer handle automatic setting of associate_user_profile_with_barcode
        # based on barcode type. No manual intervention needed here.

        serializer = UserBarcodeSettingsSerializer(
            settings,
            data=data,
            context={'request': request},
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'success',
                'message': 'Barcode settings updated successfully',
                'settings': serializer.data
            })

        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        """Create new barcode"""
        # Check if user is in User group - they shouldn't access this endpoint
        if request.user.groups.filter(name="User").exists():
            return Response({
                'detail': 'User type accounts cannot access barcode dashboard'
            }, status=status.HTTP_403_FORBIDDEN)
            
        serializer = BarcodeCreateSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            barcode = serializer.save()
            return Response({
                'status': 'success',
                'message': 'New barcode added successfully',
                'barcode': BarcodeSerializer(barcode, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)

        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Delete barcode - users may delete only their own barcodes (DynamicBarcode and Others types)"""
        # Check if user is in User group - they shouldn't access this endpoint
        if request.user.groups.filter(name="User").exists():
            return Response({
                'detail': 'User type accounts cannot access barcode dashboard'
            }, status=status.HTTP_403_FORBIDDEN)
            
        barcode_id = request.data.get('barcode_id')

        if not barcode_id:
            return Response({
                'status': 'error',
                'message': 'Barcode ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # All users can only delete barcodes they own
        try:
            barcode = Barcode.objects.get(
                pk=barcode_id,
                user=request.user,
                barcode_type__in=['DynamicBarcode', 'Others']
            )
        except Barcode.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Barcode not found or you do not have permission to delete it'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if this barcode is currently selected in settings
        settings = UserBarcodeSettings.objects.filter(
            user=request.user,
            barcode=barcode
        ).first()

        if settings:
            settings.barcode = None
            settings.save()

        barcode.delete()

        return Response({
            'status': 'success',
            'message': 'Barcode deleted successfully'
        })
