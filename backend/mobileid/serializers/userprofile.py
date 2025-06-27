from django.contrib.auth.models import User
from rest_framework import (
    serializers,
)

from mobileid.models import (
    Barcode,
    UserBarcodeSettings,
)
from .barcode import BarcodeListSerializer


class UserProfileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='studentinformation.name', required=False, allow_blank=False)
    student_id = serializers.CharField(source='studentinformation.information_id', required=False, allow_blank=False)

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
        student_info.information_id = info_data.get('information_id', student_info.information_id)
        student_info.user_profile_img = info_data.get('user_profile_img', student_info.user_profile_img)
        student_info.save()

        return super().update(instance, validated_data)


class UserBarcodeSettingsSerializer(serializers.ModelSerializer):
    available_barcodes = serializers.SerializerMethodField()

    barcode = serializers.PrimaryKeyRelatedField(
        queryset=Barcode.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = UserBarcodeSettings
        fields = [
            'barcode_pull',
            'barcode',
            'server_verification',
            'timestamp_verification',
            'available_barcodes',
        ]

    def get_available_barcodes(self, obj):
        user = obj.user
        barcodes = Barcode.objects.filter(user=user)
        return BarcodeListSerializer(barcodes, many=True).data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.context.get('request').user
        if user:
            self.fields['barcode'].queryset = Barcode.objects.filter(user=user)

    def validate(self, data):
        user = self.context['request'].user
        has_barcodes = Barcode.objects.filter(user=user).exists()

        if not has_barcodes:
            data['barcode_pull'] = True

        pull_enabled = data.get('barcode_pull', self.instance.barcode_pull if self.instance else True)
        selected_barcode = data.get('barcode')

        if not pull_enabled:
            if not selected_barcode:
                raise serializers.ValidationError({
                    "barcode": "Please select a barcode when Barcode Pull is disabled."
                })

        else:
            data['barcode'] = None

        return data
