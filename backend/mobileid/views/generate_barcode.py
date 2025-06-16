# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
#
# import random
# import pytz
# from mobileid.models import StudentInformation, UserBarcodeSettings, Barcode
# from mobileid.project_code.barcode import auto_send_code
#
#
# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def generate_barcode_view(request):
#     """
#     Generate a barcode for the current user.
#     """
#     # For demonstration purposes, we'll return a static barcode value.
#     # In a real application, you would generate a barcode based on user data.
#     barcode_data = {
#         'barcode': '1234567890123',
#         'format': 'EAN-13',
#         'message': 'This is a sample barcode for the authenticated user.'
#     }
#
#     return Response(barcode_data)