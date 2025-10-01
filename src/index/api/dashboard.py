from index.models import Barcode, UserBarcodeSettings, BarcodeUsage
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
            # School users see:
            # - Dynamic barcodes that are shared by others OR owned by themselves
            # - Their own Identification and Others barcodes
            from django.db.models import Q
            barcodes = (
                Barcode.objects.filter(
                    (
                        Q(barcode_type='DynamicBarcode') &
                        (Q(user=user) | Q(share_with_others=True))
                    )
                    |
                    Q(user=user, barcode_type__in=['Others', 'Identification'])
                )
                .select_related('user')
                .prefetch_related('barcodeuserprofile', 'barcodeusage_set')
                .order_by('-time_created')
            )
        else:
            # Other users see all of their own barcodes, including Identification
            barcodes = (
                Barcode.objects.filter(
                    user=user,
                    barcode_type__in=['DynamicBarcode', 'Others', 'Identification']
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
            # Record a transaction for barcode creation via service layer
            from index.services.transactions import TransactionService
            TransactionService.create_transaction(user=request.user, barcode=barcode)
            return Response({
                'status': 'success',
                'message': 'New barcode added successfully',
                'barcode': BarcodeSerializer(barcode, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)

        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        """Update properties of a barcode owned by the current user (share flag and daily limit)"""
        # Check if user is in User group - they shouldn't access this endpoint
        if request.user.groups.filter(name="User").exists():
            return Response({
                'detail': 'User type accounts cannot access barcode dashboard'
            }, status=status.HTTP_403_FORBIDDEN)

        barcode_id = request.data.get('barcode_id')
        share_with_others = request.data.get('share_with_others')
        daily_usage_limit = request.data.get('daily_usage_limit')

        if not barcode_id:
            return Response({
                'status': 'error',
                'message': 'barcode_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            barcode = Barcode.objects.get(
                pk=barcode_id,
                user=request.user
            )
        except Barcode.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Barcode not found or you do not have permission to update it'
            }, status=status.HTTP_404_NOT_FOUND)

        # Identification barcodes cannot be updated
        if barcode.barcode_type == 'Identification':
            return Response({
                'status': 'error',
                'message': 'Identification barcodes cannot be modified'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Update share_with_others if provided
        if share_with_others is not None:
            # Coerce to boolean if sent as string
            if isinstance(share_with_others, str):
                share_with_others = share_with_others.lower() in ['1', 'true', 'yes', 'on']
            barcode.share_with_others = bool(share_with_others)
            barcode.save()

        # Update daily_usage_limit if provided
        if daily_usage_limit is not None:
            try:
                # Ensure it's a non-negative integer
                limit_value = int(daily_usage_limit)
                if limit_value < 0:
                    return Response({
                        'status': 'error',
                        'message': 'Daily usage limit must be 0 or greater'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Get or create BarcodeUsage record
                usage, _ = BarcodeUsage.objects.get_or_create(
                    barcode=barcode,
                    defaults={'total_usage': 0}
                )
                usage.daily_usage_limit = limit_value
                usage.save()
            except (ValueError, TypeError):
                return Response({
                    'status': 'error',
                    'message': 'Daily usage limit must be a valid number'
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'success',
            'message': 'Barcode updated successfully',
            'barcode': BarcodeSerializer(barcode, context={'request': request}).data
        })

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
