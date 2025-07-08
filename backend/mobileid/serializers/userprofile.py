from django.contrib.auth.models import User
from rest_framework import (
    serializers,
)

from mobileid.models import (
    Barcode,
    UserBarcodeSettings,
    UserProfile,
)
from .barcode import BarcodeListSerializer


class StudentInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['name', 'information_id', 'user_profile_img']


class UserProfileSerializer(serializers.ModelSerializer):
    userprofile = StudentInformationSerializer()

    class Meta:
        model = User
        fields = ['username', 'userprofile']
        read_only_fields = ['username']

    def update(self, instance, validated_data):
        info_data = validated_data.pop('userprofile', {})

        student_info = getattr(instance, 'userprofile', None)
        if not student_info:
            student_info = UserProfile.objects.create(user=instance)

        for attr in ['name', 'information_id', 'user_profile_img']:
            if attr in info_data:
                setattr(student_info, attr, info_data[attr])
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
