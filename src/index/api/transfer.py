import logging

from index.project_code.transfer_barcode import TransferBarcode
from index.services.cookie import process_user_cookie
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

# Configure logging
logger = logging.getLogger(__name__)


class TransferCatCardAPIView(APIView):
    """
    API endpoint for transferring CatCard data:
    - POST: Process user's CatCard cookies and store barcode data
    
    Requires authentication and expects cookies in request data.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Process CatCard cookies and store barcode data for authenticated user"""
        try:
            # Get cookies from request data
            raw_cookies = request.data.get("cookies", "")

            if not raw_cookies:
                logger.warning("No cookies provided in transfer request")
                return Response({
                    'error': 'No cookie provided',
                    'success': False
                }, status=status.HTTP_400_BAD_REQUEST)

            # Normalize/process the user cookie
            processed = process_user_cookie(raw_cookies)
            normalized_cookie_header = processed.header_value

            # Log warnings if any
            if processed.warnings:
                logger.warning(f"Cookie processing warnings: {processed.warnings}")
                # If there are critical warnings about missing session cookies, return error
                if any("Missing required cookie" in w for w in processed.warnings):
                    return Response({
                        'error': 'Invalid cookies: ' + '; '.join(processed.warnings),
                        'success': False
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Create transfer service with current authenticated user
            service = TransferBarcode(user_cookies=normalized_cookie_header, user=request.user)
            result = service.transfer_barcode()

            logger.info(
                f"Transfer result for user {request.user.username}: {result.status} - "
                f"{result.response if result.status == 'success' else result.error}"
            )

            if result.status == 'success':
                return Response({
                    'message': result.response or 'Barcode data stored successfully',
                    'success': True
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': result.error or 'Failed to store barcode data',
                    'success': False
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"Transfer error for user {request.user.username}: {e}")
            return Response({
                'error': 'Internal server error',
                'success': False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
