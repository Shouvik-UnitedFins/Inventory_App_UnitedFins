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


# Public registration for Admin users (entry point of hierarchy)
class AdminRegistrationSerializer(serializers.ModelSerializer):
    name = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    phone_number = serializers.CharField(write_only=True, required=False, allow_blank=True)
    password = serializers.CharField(
        write_only=True, 
        min_length=8,
        error_messages={
            'min_length': 'Password must be at least 8 characters long.'
        }
    )
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    
    class Meta:
        model = User
        fields = ('name', 'email', 'phone_number', 'password', 'latitude', 'longitude')
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        name = validated_data.pop('name', '')
        phone_number = validated_data.pop('phone_number', '')
        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)
        
        user = User.objects.create(email=validated_data['email'])
        user.set_password(password)
        user.save()
        
        # Always create admin role for this endpoint
        profile = UserProfile.objects.create(user=user, role='admin')
        profile.name = name
        profile.phone_number = phone_number
        profile.latitude = latitude
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
        return data


# Protected registration for other roles (admin only - excludes admin and super_admin)
class UserRegistrationSerializer(serializers.ModelSerializer):
    # Define allowed roles for this endpoint (excluding admin and super_admin)
    ALLOWED_ROLES = [
        ('storekeeper', 'Store Keeper'),
        ('inventorymanager', 'Inventory Manager'), 
        ('requester', 'Requester'),
        ('vendor', 'Vendor'),
    ]
    
    name = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    phone_number = serializers.CharField(write_only=True, required=False, allow_blank=True)
    password = serializers.CharField(
        write_only=True, 
        min_length=8,
        error_messages={
            'min_length': 'Password must be at least 8 characters long.'
        }
    )
    role = serializers.ChoiceField(choices=ALLOWED_ROLES, write_only=True)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('name', 'email', 'phone_number', 'password', 'role', 'latitude', 'longitude')
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value
    
    def validate_role(self, value):
        # Ensure only allowed roles can be created through this endpoint
        allowed_role_keys = [role[0] for role in self.ALLOWED_ROLES]
        if value not in allowed_role_keys:
            raise serializers.ValidationError(
                f"Invalid role. Allowed roles: {', '.join(allowed_role_keys)}. "
                "Admin users must use the public admin registration endpoint."
            )
        return value

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
        profile.name = name
        profile.phone_number = phone_number
        profile.latitude = latitude
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
