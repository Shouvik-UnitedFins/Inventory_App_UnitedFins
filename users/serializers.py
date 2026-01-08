from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

# Custom serializer for email-based JWT login
from users.models import UserProfile

class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        # Add user details to the response, using UUID from profile
        data['user'] = {
            'uuid': str(user.profile.uuid) if hasattr(user, 'profile') else None,
            'email': user.email,
            'role': getattr(user.profile, 'role', None) if hasattr(user, 'profile') else None,
            'is_active': user.is_active,
        }
        return data

from rest_framework import serializers
from users.models import User
from .models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('role', 'uuid')

class UserDetailSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    class Meta:
        model = User
        fields = ('email', 'is_active', 'profile')

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'is_active')

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
        fields = ('password', 'email', 'role')

    def create(self, validated_data):
        role = validated_data.pop('role')
        password = validated_data.pop('password')
        user = User.objects.create(email=validated_data['email'])
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
