from django.contrib.auth.models import User
from rest_framework import serializers


class UserProfileSerializer(serializers.ModelSerializer):
    # Get fields from the related StudentInformation model
    name = serializers.CharField(source='studentinformation.name')
    student_id = serializers.CharField(source='studentinformation.student_id')
    user_profile_img = serializers.CharField(source='studentinformation.user_profile_img')

    class Meta:
        model = User
        fields = ['username', 'name', 'student_id', 'user_profile_img']
