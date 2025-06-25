import base64
from io import BytesIO
from PIL import Image
from django.contrib.auth import get_user_model
from rest_framework import serializers
from mobileid.models import StudentInformation, UserBarcodeSettings, Barcode

