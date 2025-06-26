from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

from mobileid.models import StudentInformation

from PIL import Image
from io import BytesIO
import base64


class RegisterSerializer(serializers.ModelSerializer):
    # extra fields
    name = serializers.CharField(max_length=100)
    student_id = serializers.CharField(max_length=100)
    user_profile_img = serializers.ImageField(write_only=True)

    class Meta:
        model = User
        fields = (
            "username", "password", "name", "student_id", "user_profile_img"
        )
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        # pop custom fields
        name = validated_data.pop("name")
        student_id = validated_data.pop("student_id")
        img_file = validated_data.pop("user_profile_img")

        # create user
        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
        )

        with Image.open(img_file) as im:
            side = min(im.size)
            left = (im.width - side) // 2
            top = (im.height - side) // 2
            im = im.crop((left, top, left + side, top + side))
            im = im.resize((128, 128), Image.LANCZOS)
            buf = BytesIO()
            im.save(buf, "PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()

        StudentInformation.objects.create(
            user=user,
            name=name,
            student_id=student_id,
            user_profile_img=b64,
        )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        if not username or not password:
            raise serializers.ValidationError("Both username and password are required")

        user = authenticate(
            username=username,
            password=password
        )
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        attrs["user"] = user
        return attrs
