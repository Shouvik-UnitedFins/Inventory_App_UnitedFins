
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('role', 'uuid')

class UserDetailSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_active', 'profile')

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'is_active')

class UserStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('is_active',)

class UserPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

class UserRegistrationSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, write_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'email', 'role')

    def create(self, validated_data):
        role = validated_data.pop('role')
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        UserProfile.objects.create(user=user, role=role)
        return user

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Add role and uuid from profile if it exists
        profile = getattr(instance, 'profile', None)
        if profile:
            data['role'] = profile.role
            data['uuid'] = str(profile.uuid)
        else:
            data['role'] = None
            data['uuid'] = None
        return data
