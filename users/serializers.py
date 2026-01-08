from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

# Custom serializer for email-based JWT login
from users.models import UserProfile

class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'

    def validate(self, attrs):
        try:
            from django.contrib.auth import authenticate
            email = attrs.get('email')
            password = attrs.get('password')
            if not email or not password:
                raise serializers.ValidationError({'message': 'Email and password are required.'})
            user = authenticate(request=self.context.get('request'), username=email, password=password)
            if user is None:
                # Check if user exists for better error
                from users.models import User
                try:
                    user_obj = User.objects.get(email=email)
                    if not user_obj.check_password(password):
                        raise serializers.ValidationError({'message': 'Invalid password.'})
                    if not user_obj.is_active:
                        raise serializers.ValidationError({'message': 'User account is inactive.'})
                    if hasattr(user_obj, 'profile') and getattr(user_obj.profile, 'blocked', False):
                        raise serializers.ValidationError({'message': 'User account is blocked.'})
                except User.DoesNotExist:
                    raise serializers.ValidationError({'message': 'User with this email does not exist.'})
                raise serializers.ValidationError({'message': 'Authentication failed.'})
            if not user.is_active:
                raise serializers.ValidationError({'message': 'User account is inactive.'})
            if hasattr(user, 'profile') and getattr(user.profile, 'blocked', False):
                raise serializers.ValidationError({'message': 'User account is blocked.'})
            data = super().validate(attrs)
            data['user'] = {
                'uuid': str(user.profile.uuid) if hasattr(user, 'profile') else None,
                'email': user.email,
                'role': getattr(user.profile, 'role', None) if hasattr(user, 'profile') else None,
                'is_active': user.is_active,
            }
            return data
        except Exception as e:
            import traceback
            print('LOGIN ERROR:', traceback.format_exc())
            raise serializers.ValidationError({'message': f'Login failed: {str(e)}'})

from rest_framework import serializers
from users.models import User
from .models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('role', 'uuid', 'blocked')

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
            data['blocked'] = profile.blocked
        else:
            data['role'] = None
            data['uuid'] = None
            data['latitude'] = None
            data['longitude'] = None
            data['blocked'] = None
        return data
