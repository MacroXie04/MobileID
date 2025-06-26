from django.contrib.auth.models import User

from rest_framework import (
    serializers,
    generics,
)


class UserProfileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='studentinformation.name', required=False, allow_blank=False)
    student_id = serializers.CharField(source='studentinformation.student_id', required=False, allow_blank=False)


    user_profile_img = serializers.CharField(source='studentinformation.user_profile_img', required=False,
                                             allow_blank=False)

    class Meta:
        model = User
        fields = [
            'username',
            'name',
            'student_id',
            'user_profile_img'
        ]
        read_only_fields = ['username']

    def update(self, instance, validated_data):
        info_data = validated_data.pop('studentinformation', {})
        student_info = instance.studentinformation
        student_info.name = info_data.get('name', student_info.name)
        student_info.student_id = info_data.get('student_id', student_info.student_id)
        student_info.user_profile_img = info_data.get('user_profile_img', student_info.user_profile_img)
        student_info.save()

        return super().update(instance, validated_data)

