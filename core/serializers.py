from rest_framework import serializers
from .models import Organisation, BusinessUnit, Department, User


class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = ['id', 'name', 'slug', 'address', 'phone', 'email', 'logo', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class BusinessUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessUnit
        fields = ['id', 'organisation', 'name', 'unit_type', 'description', 'is_active']
        read_only_fields = ['id']


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'organisation', 'business_unit', 'name', 'description', 'is_active']
        read_only_fields = ['id']


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'role', 'organisation', 'department',
            'avatar', 'is_active', 'date_joined',
            'notify_email', 'notify_sms', 'notify_push', 'notify_whatsapp',
        ]
        read_only_fields = ['id', 'date_joined']

    def get_full_name(self, obj):
        return obj.get_full_name()


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'phone',
            'role', 'organisation', 'department',
            'password', 'confirm_password',
        ]

    def validate(self, data):
        if data['password'] != data.pop('confirm_password'):
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
