from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import serializers

from mobileid.models import UserProfile


class RegisterSerializer(serializers.ModelSerializer):
    name = serializers.CharField(write_only=True, required=True, max_length=100)
    information_id = serializers.CharField(
        write_only=True, required=True, max_length=100
    )
    user_profile_img = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(
        write_only=True, required=True, label="Confirm Password"
    )

    class Meta:
        model = User
        fields = [
            "username",
            "password",
            "password2",
            "name",
            "information_id",
            "user_profile_img",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, attrs):
        # check if passwords match
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password2": "Passwords do not match."})

        # create a temporary user instance to validate the password
        temp_user = User(username=attrs["username"])

        try:
            validate_password(attrs["password"], user=temp_user)
        except ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        return attrs

    def create(self, validated_data):
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=validated_data["username"],
                    password=validated_data["password"],
                    # new user is not active
                    is_active=False,
                )
                UserProfile.objects.create(
                    user=user,
                    name=validated_data["name"],
                    information_id=validated_data["information_id"],
                    user_profile_img=validated_data["user_profile_img"],
                )
                return user
        except Exception as e:
            raise serializers.ValidationError(
                {"detail": f"An error occurred during registration: {str(e)}"}
            )
