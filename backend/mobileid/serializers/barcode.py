from django.contrib.auth.models import User

from rest_framework import (
    serializers,
    generics,
)

from mobileid.project_code.barcode import (
    uc_merced_mobile_id,
    auto_send_code,
)

from mobileid.models import (
    Barcode,
    BarcodeUsage,
    UserBarcodeSettings,
)

from barcode.settings import SELENIUM_ENABLED


class BarcodeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Barcode
        fields = ['id', 'barcode_type', 'barcode', 'student_id']


class BarcodeCreateSerializer(serializers.Serializer):
    source_type = serializers.ChoiceField(choices=[('barcode', 'Barcode'), ('session', 'Session')])
    input_value = serializers.CharField(max_length=255, allow_blank=False)

    def validate_input_value(self, value):
        source_type = self.initial_data.get('source_type')
        if source_type == 'barcode':
            if not value.isdigit():
                raise serializers.ValidationError("Barcode can only contain digits.")
            if len(value) not in (16, 28):
                raise serializers.ValidationError("Barcode length must be 16 or 28.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        src_type = validated_data['source_type']
        input_val = validated_data['input_value']

        if src_type == "barcode":
            code_to_check = input_val if len(input_val) == 16 else input_val[-14:]
            if Barcode.objects.filter(barcode=code_to_check, user=user).exists():
                raise serializers.ValidationError({"input_value": "This barcode already exists."})

            barcode_type = "Static" if len(input_val) == 16 else "Dynamic"
            barcode_value = input_val if len(input_val) == 16 else input_val[-14:]

            barcode_obj = Barcode.objects.create(
                user=user, barcode_type=barcode_type, barcode=barcode_value, student_id=""
            )

        elif src_type == "session":
            if not SELENIUM_ENABLED:
                raise serializers.ValidationError({"source_type": "This feature is currently disabled."})

            result = uc_merced_mobile_id(input_val)
            code = result.get("barcode")
            if not code:
                raise serializers.ValidationError({"input_value": "Failed to retrieve barcode from session."})

            barcode_obj, created = Barcode.objects.get_or_create(
                barcode=code,
                defaults={"user": user, "barcode_type": "Dynamic", "session": input_val, "id": ""}
            )
            if not created:
                barcode_obj.user = user
                barcode_obj.session = input_val
                barcode_obj.save()
        else:
            raise serializers.ValidationError("Invalid source type.")

        UserBarcodeSettings.objects.update_or_create(user=user, defaults={"barcode": barcode_obj})
        BarcodeUsage.objects.get_or_create(barcode=barcode_obj)

        return barcode_obj

