from rest_framework import serializers
from django.contrib.auth.models import Group
from mobileid.models import Barcode, UserBarcodeSettings, BarcodeUsage


class BarcodeSerializer(serializers.ModelSerializer):
    """Serializer for listing barcodes"""
    usage_count = serializers.SerializerMethodField()
    last_used = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Barcode
        fields = ['id', 'barcode_type', 'barcode', 'time_created', 'usage_count', 'last_used', 'display_name']
        read_only_fields = ['id', 'barcode_type', 'time_created']
    
    def get_usage_count(self, obj):
        """Get total usage count for the barcode"""
        try:
            return obj.barcodeusage_set.first().total_usage
        except:
            return 0
    
    def get_last_used(self, obj):
        """Get last used timestamp for the barcode"""
        try:
            return obj.barcodeusage_set.first().last_used
        except:
            return None
    
    def get_display_name(self, obj):
        """Get display name for the barcode based on its type"""
        if obj.barcode_type == 'Identification':
            return f"{obj.user.username}'s identification barcode"
        elif obj.barcode_type == 'DynamicBarcode':
            return f"Dynamic Barcode ending with {obj.barcode[-4:]}"
        else:  # Others type (Static Barcode)
            return f"Barcode ending with {obj.barcode[-4:]}"


class BarcodeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new barcodes"""
    
    class Meta:
        model = Barcode
        fields = ['barcode']
    
    def validate_barcode(self, value):
        """Clean and validate barcode"""
        return value.strip()
    
    def create(self, validated_data):
        """Create barcode with automatic type detection"""
        user = self.context['request'].user
        barcode_value = validated_data['barcode']
        
        # Check if 28-digit numeric and user is in School group
        is_28_digit = len(barcode_value) == 28 and barcode_value.isdigit()
        is_school = user.groups.filter(name="School").exists()
        
        if is_28_digit and is_school:
            # Dynamic barcode - save only last 14 digits
            barcode_type = "DynamicBarcode"
            barcode_value = barcode_value[-14:]
        else:
            # Other barcode type
            barcode_type = "Others"
        
        return Barcode.objects.create(
            user=user,
            barcode=barcode_value,
            barcode_type=barcode_type
        )


class UserBarcodeSettingsSerializer(serializers.ModelSerializer):
    """Serializer for user barcode settings"""
    barcode_choices = serializers.SerializerMethodField()
    field_states = serializers.SerializerMethodField()
    
    class Meta:
        model = UserBarcodeSettings
        fields = ['barcode', 'barcode_pull', 'server_verification', 'barcode_choices', 'field_states']
    
    def get_barcode_choices(self, obj):
        """Get available barcode choices for the user"""
        user = self.context['request'].user
        barcodes = Barcode.objects.filter(user=user).order_by('-time_created')
        choices = []
        
        for b in barcodes:
            if b.barcode_type == 'Identification':
                display = f"{user.username}'s identification barcode"
            elif b.barcode_type == 'DynamicBarcode':
                display = f"Dynamic Barcode ending with {b.barcode[-4:]}"
            else:  # Others type (Static Barcode)
                display = f"Barcode ending with {b.barcode[-4:]}"
            
            choices.append({
                'id': b.id,
                'display': display,
                'barcode': b.barcode,
                'barcode_type': b.barcode_type,
                'full_display': f"{b.barcode_type} - {b.barcode}"
            })
        
        return choices
    
    def get_field_states(self, obj):
        """Get field states based on user group and current settings"""
        user = self.context['request'].user
        is_user_group = user.groups.filter(name="User").exists()
        
        return {
            'barcode_pull_disabled': is_user_group,  # Rule 1: User group cannot enable pull
            'barcode_disabled': obj.barcode_pull if obj else False  # Rule 2: When pull is ON, barcode is disabled
        }
    
    def validate(self, data):
        """Validate settings based on user group and pull setting"""
        user = self.context['request'].user
        
        # Check if user is in "User" group
        is_user_group = user.groups.filter(name="User").exists()
        
        # Rule 1: Standard users cannot enable barcode pull
        if is_user_group and data.get('barcode_pull', False):
            raise serializers.ValidationError({
                'barcode_pull': 'Standard users cannot enable automatic barcode pull.'
            })
        
        # Rule 2: When pull is ON, barcode must be empty
        if data.get('barcode_pull', False) and data.get('barcode'):
            data['barcode'] = None  # Clear barcode when pull is enabled
        
        return data 