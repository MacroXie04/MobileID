from index.services.barcode import generate_barcode
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class GenerateBarcodeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        result = generate_barcode(request.user)
        return Response(result, status=200)
