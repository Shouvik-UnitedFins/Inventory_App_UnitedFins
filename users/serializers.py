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

    name = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    phone_number = serializers.CharField(write_only=True, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, write_only=True)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)


    class Meta:
        model = User
        fields = ('name', 'email', 'phone_number', 'password', 'role', 'latitude', 'longitude')

    def create(self, validated_data):
        role = validated_data.pop('role')
        password = validated_data.pop('password')
        name = validated_data.pop('name', '')
        phone_number = validated_data.pop('phone_number', '')
        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)
        user = User.objects.create(email=validated_data['email'])
        user.set_password(password)
        user.save()
        profile = UserProfile.objects.create(user=user, role=role)
        # Optionally save extra fields to profile if you add them to the model
        if hasattr(profile, 'name'):
            profile.name = name
        if hasattr(profile, 'phone_number'):
            profile.phone_number = phone_number
        if hasattr(profile, 'latitude'):
            profile.latitude = latitude
        if hasattr(profile, 'longitude'):
            profile.longitude = longitude
        profile.save()
        return user

    def to_representation(self, instance):
        data = super().to_representation(instance)
        profile = getattr(instance, 'profile', None)
        if profile:
            data['role'] = profile.role
            data['uuid'] = str(profile.uuid)
            data['latitude'] = profile.latitude
            data['longitude'] = profile.longitude
        else:
            data['role'] = None
            data['uuid'] = None
            data['latitude'] = None
            data['longitude'] = None
        return data
