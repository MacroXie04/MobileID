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
    1. If user is in "User" group: barcode_pull is permanently False and disabled
    2. When barcode_pull is True, barcode field must be disabled and cleared
    3. Only DynamicBarcode and Others types can be managed
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user settings and barcodes"""
        user = request.user

        # Get or create user settings
        settings, created = UserBarcodeSettings.objects.get_or_create(
            user=user,
            defaults={
                'barcode': None,
                'server_verification': False,
                'barcode_pull': False
            }
        )

        # Force barcode_pull to False for User group members
        is_user_group = user.groups.filter(name="User").exists()
        if is_user_group and settings.barcode_pull:
            settings.barcode_pull = False
            settings.save()

        # Get user's barcodes (excluding Identification type)
        barcodes = Barcode.objects.filter(
            user=user,
            barcode_type__in=['DynamicBarcode', 'Others']
        ).order_by('-time_created')

        # Serialize data
        settings_serializer = UserBarcodeSettingsSerializer(
            settings,
            context={'request': request}
        )
        barcodes_serializer = BarcodeSerializer(barcodes, many=True)

        return Response({
            'settings': settings_serializer.data,
            'barcodes': barcodes_serializer.data,
            'is_user_group': is_user_group,
            'is_school_group': user.groups.filter(name="School").exists()
        })

    def post(self, request):
        """Update user barcode settings"""
        user = request.user
        settings, _ = UserBarcodeSettings.objects.get_or_create(user=user)

        # Create a copy of request data to potentially modify
        data = request.data.copy()

        # Rule 1: Force barcode_pull to False for User group
        is_user_group = user.groups.filter(name="User").exists()
        if is_user_group:
            data['barcode_pull'] = False

        # Rule 2: Clear barcode when barcode_pull is True
        if data.get('barcode_pull', False):
            data['barcode'] = None

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
        serializer = BarcodeCreateSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            barcode = serializer.save()
            return Response({
                'status': 'success',
                'message': 'New barcode added successfully',
                'barcode': BarcodeSerializer(barcode).data
            }, status=status.HTTP_201_CREATED)

        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Delete barcode - only allows DynamicBarcode and Others types"""
        barcode_id = request.data.get('barcode_id')

        if not barcode_id:
            return Response({
                'status': 'error',
                'message': 'Barcode ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get barcode and verify ownership and type
        try:
            barcode = Barcode.objects.get(
                pk=barcode_id,
                user=request.user,
                barcode_type__in=['DynamicBarcode', 'Others']
            )
        except Barcode.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Barcode not found or cannot be deleted'
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
