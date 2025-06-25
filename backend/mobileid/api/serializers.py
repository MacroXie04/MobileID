import base64
from io import BytesIO
from PIL import Image
from django.contrib.auth import get_user_model
from rest_framework import serializers
from mobileid.models import StudentInformation, UserBarcodeSettings, Barcode
User = get_user_model()

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField(required=False, allow_blank=True)
    name = serializers.CharField(max_length=100)
    student_id = serializers.CharField(max_length=100)
    user_profile_img = serializers.ImageField(required=True)

    def create(self, validated_data):
        # create a new user
        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            email=validated_data.get("email", "")
        )

        # process the user profile image
        img_file = validated_data.pop("user_profile_img")
        with Image.open(img_file) as im:
            min_side = min(im.width, im.height)
            left = (im.width - min_side) // 2
            top = (im.height - min_side) // 2
            im = im.crop((left, top, left + min_side, top + min_side))
            im = im.resize((128, 128), Image.Resampling.LANCZOS)

            buf = BytesIO()
            im.save(buf, format="PNG")
            img_bytes = buf.getvalue()
            b64_str = base64.b64encode(img_bytes).decode()

        # creat StudentInformation object
        StudentInformation.objects.create(
            user=user,
            name=validated_data["name"],
            student_id=validated_data["student_id"],
            user_profile_img=b64_str,
        )
        return user

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'username': instance.username,
        }


class StudentInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentInformation
        fields = ("name", "student_id", "user_profile_img")


class CurrentUserSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField(allow_blank=True)
    # Note: user_profile_img is a base64 encoded PNG image
    name = serializers.CharField()
    student_id = serializers.CharField()
    user_profile_img = serializers.CharField()
