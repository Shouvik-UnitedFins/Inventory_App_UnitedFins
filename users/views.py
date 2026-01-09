from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.views import TokenRefreshView

# Custom TokenRefreshView for Swagger grouping
@extend_schema(tags=["Token"], description="Obtain a new access token using a valid refresh token.")
class CustomTokenRefreshView(TokenRefreshView):
	pass
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import EmailTokenObtainPairSerializer

# Custom view for email-based JWT login
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import extend_schema

@extend_schema(tags=["Auth"])
class EmailTokenObtainPairView(TokenObtainPairView):
	serializer_class = EmailTokenObtainPairSerializer

	def post(self, request, *args, **kwargs):
		response = super().post(request, *args, **kwargs)
		# If login is successful, add a message
		if response.status_code == 200:
			response.data['message'] = 'Login successful'
		else:
			# For error, ensure message is present
			if 'detail' in response.data:
				response.data['message'] = response.data['detail']
				del response.data['detail']
		return response
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
User = get_user_model()
from .serializers import UserDetailSerializer, UserUpdateSerializer, UserStatusSerializer, UserPasswordSerializer
# User management viewset (CRUD, status, password)


from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiTypes
from .auditlog import AuditLog
from django_filters.rest_framework import DjangoFilterBackend

@extend_schema_view(
	list=extend_schema(
		summary="List all users",
		tags=["Users"],
		parameters=[
			OpenApiParameter(
				name="role",
				type=OpenApiTypes.STR,
				location=OpenApiParameter.QUERY,
				description="Filter users by role. Valid values: super_admin, admin, store_keeper, inventory_manager, requester, vendor."
			),
		],
		description="Retrieve a list of users. You can filter by role using the 'role' query parameter."
	),
	retrieve=extend_schema(summary="Retrieve a user by UUID.", tags=["Users"], description="Get details for a specific user by their UUID."),
	update=extend_schema(summary="Update a user", tags=["Users"], description="Update all fields for a user."),
	partial_update=extend_schema(summary="Partially update a user", tags=["Users"], description="Update one or more fields for a user."),
	set_status=extend_schema(summary="Update user status", tags=["Users"], description="Update the active status of a user."),
	set_password=extend_schema(summary="Set user password", tags=["Users"], description="Set a new password for a user (admin only)."),
)

class UserViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):

	@extend_schema(
		summary="Change own password",
		tags=["Users"],
		description="Allow authenticated users to change their own password."
	)
	@action(detail=False, methods=['post'], url_path='change-password', permission_classes=[IsAuthenticated])
	def change_password(self, request):
		"""Allow authenticated users to change their own password."""
		user = request.user
		serializer = UserPasswordSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		user.set_password(serializer.validated_data['password'])
		user.save()
		# Audit log
		AuditLog.objects.create(user=user, action="change_password", details="User changed their password")
		return Response({'message': 'Password changed successfully'})

	@extend_schema(
		summary="Block a user",
		tags=["Users"],
		description="Block a user by email or name. Only admin/super_admin can perform this action."
	)
	@action(detail=False, methods=['patch'], url_path='block', permission_classes=[IsAuthenticated])
	def block(self, request):
		"""Block a user by email or name (admin only)."""
		current_user = request.user
		if not hasattr(current_user, 'profile') or current_user.profile.role != 'admin':
			return Response({'message': 'You do not have permission to block users. Only admin can perform this action.', 'data': None}, status=status.HTTP_403_FORBIDDEN)
		identifier = request.data.get('email') or request.data.get('name')
		if not identifier:
			return Response({'message': 'Provide email or name to block user.', 'data': None}, status=status.HTTP_400_BAD_REQUEST)
		from users.models import User, UserProfile
		user = None
		if request.data.get('email'):
			user = User.objects.filter(email=request.data['email']).first()
		elif request.data.get('name'):
			user_profile = UserProfile.objects.filter(name=request.data['name']).first()
			user = user_profile.user if user_profile else None
		if user and hasattr(user, 'profile'):
			user.profile.blocked = True
			user.profile.save()
			AuditLog.objects.create(user=current_user, action="block", details=f"Blocked user {user.email}")
			return Response({'message': 'User blocked successfully', 'data': None})
		return Response({'message': 'User not found or profile missing', 'data': None}, status=status.HTTP_404_NOT_FOUND)

	@extend_schema(
		summary="Unblock a user",
		tags=["Users"],
		description="Unblock a user by email or name. Only admin/super_admin can perform this action."
	)
	@action(detail=False, methods=['patch'], url_path='unblock', permission_classes=[IsAuthenticated])
	def unblock(self, request):
		"""Unblock a user by email or name (admin only)."""
		current_user = request.user
		if not hasattr(current_user, 'profile') or current_user.profile.role != 'admin':
			return Response({'message': 'You do not have permission to unblock users. Only admin can perform this action.', 'data': None}, status=status.HTTP_403_FORBIDDEN)
		identifier = request.data.get('email') or request.data.get('name')
		if not identifier:
			return Response({'message': 'Provide email or name to unblock user.', 'data': None}, status=status.HTTP_400_BAD_REQUEST)
		from users.models import User, UserProfile
		user = None
		if request.data.get('email'):
			user = User.objects.filter(email=request.data['email']).first()
		elif request.data.get('name'):
			user_profile = UserProfile.objects.filter(name=request.data['name']).first()
			user = user_profile.user if user_profile else None
		if user and hasattr(user, 'profile'):
			user.profile.blocked = False
			user.profile.save()
			AuditLog.objects.create(user=current_user, action="unblock", details=f"Unblocked user {user.email}")
			return Response({'message': 'User unblocked successfully', 'data': None})
		return Response({'message': 'User not found or profile missing', 'data': None}, status=status.HTTP_404_NOT_FOUND)

	"""API endpoints for managing users."""
	queryset = get_user_model().objects.all()
	serializer_class = UserDetailSerializer
	permission_classes = [IsAuthenticated]
	lookup_field = 'profile__uuid'
	lookup_url_kwarg = 'id'  # URL parameter name
	lookup_value_regex = '[0-9a-fA-F-]+'
	filter_backends = [DjangoFilterBackend]
	filterset_fields = ['profile__role']

	@extend_schema(
		summary="Delete a user",
		description="Delete a user by ID. Only users with the 'admin' role can perform this action. Master Admin and all other roles are not allowed to delete users.",
		tags=["Users"]
	)
	def destroy(self, request, *args, **kwargs):
		current_user = request.user
		# Only allow admin to delete users
		if not hasattr(current_user, 'profile') or current_user.profile.role != 'admin':
			return Response({
				'message': 'You do not have permission to delete users. Only admins can perform this action.',
				'data': None
			}, status=status.HTTP_403_FORBIDDEN)
		user = self.get_object()
		super().destroy(request, *args, **kwargs)
		# Audit log
		AuditLog.objects.create(user=current_user, action="delete", details=f"Deleted user {user.email}")
		return Response({
			'message': 'User deleted successfully',
			'data': None
		}, status=status.HTTP_200_OK)

	def get_queryset(self):
		"""Filter users based on role query parameter and user permissions"""
		queryset = super().get_queryset().select_related('profile')
		role = self.request.query_params.get('role')
		if role:
			queryset = queryset.filter(profile__role=role)
		current_user = self.request.user
		if hasattr(current_user, 'profile'):
			current_role = current_user.profile.role
			if current_role == 'admin':
				# Admin can see all users (hierarchy starts from admin)
				return queryset
			else:
				# Other roles can only see themselves
				return queryset.filter(id=current_user.id)
		return queryset.filter(id=current_user.id)

	def get_serializer_class(self):
		if self.action == 'update' or self.action == 'partial_update':
			return UserUpdateSerializer
		if self.action == 'set_status':
			return UserStatusSerializer
		if self.action == 'set_password':
			return UserPasswordSerializer
		return UserDetailSerializer


	def list(self, request, *args, **kwargs):
		response = super().list(request, *args, **kwargs)
		return Response({
			'message': 'Users fetched successfully',
			'data': response.data
		}, status=response.status_code)

	def retrieve(self, request, *args, **kwargs):
		try:
			instance = self.get_object()
			serializer = self.get_serializer(instance)
			data = serializer.data
			# Add extra fields for frontend convenience
			profile = getattr(instance, 'profile', None)
			if profile:
				data['name'] = getattr(profile, 'name', None)
				data['role'] = getattr(profile, 'role', None)
				data['blocked'] = getattr(profile, 'blocked', None)
				data['uuid'] = str(getattr(profile, 'uuid', ''))
			return Response({
				'message': 'User fetched successfully',
				'data': data,
				'error': None
			}, status=200)
		except self.queryset.model.DoesNotExist:
			return Response({
				'message': 'User not found',
				'data': None,
				'error': 'not_found'
			}, status=404)
		except Exception as e:
			return Response({
				'message': 'An error occurred',
				'data': None,
				'error': str(e)
			}, status=500)

	def update(self, request, *args, **kwargs):
		response = super().update(request, *args, **kwargs)
		return Response({
			'message': 'User updated successfully',
			'data': response.data
		}, status=response.status_code)

	def partial_update(self, request, *args, **kwargs):
		response = super().partial_update(request, *args, **kwargs)
		return Response({
			'message': 'User updated successfully',
			'data': response.data
		}, status=response.status_code)


	@action(detail=True, methods=['patch'], url_path='status')
	def set_status(self, request, pk=None):
		user = self.get_object()
		serializer = self.get_serializer(user, data=request.data, partial=True)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		return Response({'message': 'User status updated successfully'})

	@action(detail=True, methods=['patch'], url_path='password')
	def set_password(self, request, pk=None):
		"""Set password for a user (admin only)."""
		try:
			current_user = request.user
			print(f"DEBUG: Current user: {current_user.email}, Role: {getattr(current_user.profile, 'role', 'No profile')}")
			print(f"DEBUG: Request data: {request.data}")
			print(f"DEBUG: pk parameter: {pk}")
			
			if not hasattr(current_user, 'profile') or current_user.profile.role != 'admin':
				return Response({
					'message': 'You do not have permission to set passwords for other users. Only admin can perform this action.',
					'data': None
				}, status=status.HTTP_403_FORBIDDEN)
			
			print("DEBUG: Getting target user...")
			user = self.get_object()
			print(f"DEBUG: Target user: {user.email}")
			
			print("DEBUG: Validating serializer...")
			serializer = UserPasswordSerializer(data=request.data)
			serializer.is_valid(raise_exception=True)
			
			print("DEBUG: Setting password...")
			user.set_password(serializer.validated_data['password'])
			user.save()
			
			print("DEBUG: Creating audit log...")
			AuditLog.objects.create(user=current_user, action="change_password", details=f"Admin changed password for user {user.email}")
			
			return Response({'message': 'Password set successfully', 'data': None})
		except Exception as e:
			import traceback
			print(f"DEBUG ERROR: {str(e)}")
			print(f"DEBUG TRACEBACK: {traceback.format_exc()}")
			return Response({'message': f'Error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status
from users.models import User

# Logout API (blacklist refresh token)
from rest_framework.generics import GenericAPIView
from rest_framework import serializers

class LogoutSerializer(serializers.Serializer):
	refresh = serializers.CharField()

@extend_schema(
	tags=["Auth"],
	summary="Logout user (JWT)",
	description="""
	**Frontend Best Practice:**
	- On logout, always delete the access and refresh tokens from browser storage (localStorage, sessionStorage, cookies, etc.).
	- This is the main way to log out a user in a JWT-based system.
	- Optionally, call this endpoint to blacklist the refresh token for extra security (prevents reuse if stolen).
	- The backend cannot fully log out a user by itself; deleting tokens on the frontend is required.
	"""
)
class LogoutView(GenericAPIView):
	permission_classes = [IsAuthenticated]
	serializer_class = LogoutSerializer

	def post(self, request):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		try:
			refresh_token = serializer.validated_data["refresh"]
			token = RefreshToken(refresh_token)
			token.blacklist()
			return Response({"message": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT)
		except Exception as e:
			return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

from .serializers import UserDetailSerializer
# Get logged-in user API
@extend_schema(tags=["Auth"])
class MeView(GenericAPIView):
	permission_classes = [IsAuthenticated]
	serializer_class = UserDetailSerializer

	def get(self, request):
		serializer = self.get_serializer(request.user)
		return Response({
			'message': 'User profile fetched successfully',
			'data': serializer.data
		})
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile
from .serializers import UserRegistrationSerializer, AdminRegistrationSerializer

class IsAdminUserCustom(permissions.BasePermission):
	def has_permission(self, request, view):
		return (
			request.user.is_authenticated and 
			hasattr(request.user, 'profile') and 
			request.user.profile.role in ['admin']
		)

# Public registration for Admin users (no authentication required)
@extend_schema(
	tags=["Auth"],
	summary="Register Admin User (Public)",
	description="""Public endpoint to register admin users. This is the entry point of the hierarchy.
	
	Admin users can register directly without requiring super_admin approval.
	Once registered, admin users can create other role users through the protected registration endpoint.
	
	Hierarchy: Admin → (store_keeper, inventory_manager, requester, vendor)
	"""
)
class AdminRegistrationView(generics.CreateAPIView):
	from django.contrib.auth import get_user_model
	queryset = get_user_model().objects.all()
	serializer_class = AdminRegistrationSerializer
	permission_classes = []  # No authentication required

	def create(self, request, *args, **kwargs):
		response = super().create(request, *args, **kwargs)
		if response.status_code == 201:
			return Response({
				'message': 'Admin registration successful! You can now login and manage other users.',
				'data': response.data
			}, status=response.status_code)
		return response

# Protected registration for other roles (admin only)
@extend_schema(
	tags=["Auth"],
	summary="Register Users (Admin Only)",
	description="""Protected endpoint for admins to register other role users.
	
	Only admin users can create: store_keeper, inventory_manager, requester, vendor
	Super_admin is not involved in user creation - the hierarchy starts from admin.
	"""
)
class UserRegistrationView(generics.CreateAPIView):
	from django.contrib.auth import get_user_model
	queryset = get_user_model().objects.all()
	serializer_class = UserRegistrationSerializer
	permission_classes = [IsAdminUserCustom]  # Only admin can create other users

	def create(self, request, *args, **kwargs):
		response = super().create(request, *args, **kwargs)
		if response.status_code == 201:
			return Response({
				'message': 'User registration successful',
				'data': response.data
			}, status=response.status_code)
		return response

# Two-Factor Authentication Views for Password Reset
from django.utils import timezone
from datetime import timedelta
from .models import PasswordResetOTP
import random

@extend_schema(
	tags=["2FA"],
	summary="Request OTP for Password Reset (2FA)",
	description="""Request OTP via SMS or Google Authenticator for secure password reset.
	
	Supports both SMS OTP and Google Authenticator TOTP.
	OTP expires in 10 minutes for security.
	"""
)
class RequestPasswordResetOTPView(generics.GenericAPIView):
	permission_classes = []  # No authentication required
	
	class RequestOTPSerializer(serializers.Serializer):
		email = serializers.EmailField()
		otp_method = serializers.ChoiceField(choices=['sms', 'authenticator'], default='sms')
		
	serializer_class = RequestOTPSerializer
	
	def post(self, request):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		
		email = serializer.validated_data['email']
		otp_method = serializer.validated_data['otp_method']
		
		try:
			from django.contrib.auth import get_user_model
			User = get_user_model()
			user = User.objects.get(email=email)
			
			if not hasattr(user, 'profile'):
				return Response({
					'message': 'User profile not found',
					'data': None
				}, status=status.HTTP_404_NOT_FOUND)
			
			profile = user.profile
			
			if otp_method == 'sms':
				# SMS OTP Method
				if not profile.phone_number:
					return Response({
						'message': 'Phone number not registered for this account',
						'data': None
					}, status=status.HTTP_400_BAD_REQUEST)
				
				# Generate 6-digit OTP
				otp_code = PasswordResetOTP.generate_otp()
				
				# Create OTP record
				otp_record = PasswordResetOTP.objects.create(
					user=user,
					otp_code=otp_code,
					expires_at=timezone.now() + timedelta(minutes=10),
					request_type='password_reset'
				)
				
				# In production, send SMS here
				# send_sms(profile.phone_number, f"Your password reset OTP: {otp_code}")
				
				return Response({
					'message': 'OTP sent to your registered phone number',
					'data': {
						'method': 'sms',
						'phone_masked': f"***{profile.phone_number[-4:]}" if len(profile.phone_number) > 4 else "***",
						'expires_in': '10 minutes',
						'otp_for_dev': otp_code  # Remove in production
					}
				}, status=status.HTTP_200_OK)
			
			elif otp_method == 'authenticator':
				# Google Authenticator Method
				if not profile.is_2fa_enabled or not profile.totp_secret:
					return Response({
						'message': '2FA not enabled for this account. Please contact administrator.',
						'data': None
					}, status=status.HTTP_400_BAD_REQUEST)
				
				return Response({
					'message': 'Enter the 6-digit code from your Google Authenticator app',
					'data': {
						'method': 'authenticator',
						'expires_in': '30 seconds (TOTP)',
						'backup_codes_available': len(profile.otp_backup_codes) > 0
					}
				}, status=status.HTTP_200_OK)
			
		except User.DoesNotExist:
			# Return same response for security (don't reveal if email exists)
			return Response({
				'message': 'If the email exists, OTP will be sent',
				'data': {
					'method': otp_method,
					'expires_in': '10 minutes'
				}
			}, status=status.HTTP_200_OK)

@extend_schema(
	tags=["2FA"],
	summary="Verify OTP and Reset Password",
	description="""Verify OTP (SMS or Google Authenticator) and reset password.
	
	Supports both SMS OTP and Google Authenticator TOTP codes.
	Also supports backup codes for emergency access.
	"""
)
class VerifyOTPResetPasswordView(generics.GenericAPIView):
	permission_classes = []  # No authentication required
	
	class VerifyOTPSerializer(serializers.Serializer):
		email = serializers.EmailField()
		otp_code = serializers.CharField(min_length=6, max_length=6)
		new_password = serializers.CharField(min_length=6)
		confirm_password = serializers.CharField(min_length=6)
		is_backup_code = serializers.BooleanField(default=False)
		
		def validate(self, attrs):
			if attrs['new_password'] != attrs['confirm_password']:
				raise serializers.ValidationError("Passwords do not match")
			return attrs
			
	serializer_class = VerifyOTPSerializer
	
	def post(self, request):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		
		email = serializer.validated_data['email']
		otp_code = serializer.validated_data['otp_code']
		new_password = serializer.validated_data['new_password']
		is_backup_code = serializer.validated_data['is_backup_code']
		
		try:
			from django.contrib.auth import get_user_model
			User = get_user_model()
			user = User.objects.get(email=email)
			profile = user.profile
			
			if is_backup_code:
				# Verify backup code
				if otp_code in profile.otp_backup_codes:
					# Remove used backup code
					profile.otp_backup_codes.remove(otp_code)
					profile.save()
					
					# Reset password
					user.set_password(new_password)
					user.save()
					
					return Response({
						'message': 'Password reset successful using backup code. Please login with your new password.',
						'data': {
							'backup_codes_remaining': len(profile.otp_backup_codes)
						}
					}, status=status.HTTP_200_OK)
				else:
					return Response({
						'message': 'Invalid backup code',
						'data': None
					}, status=status.HTTP_400_BAD_REQUEST)
			
			# Check SMS OTP
			sms_otp = PasswordResetOTP.objects.filter(
				user=user,
				otp_code=otp_code,
				is_used=False,
				request_type='password_reset'
			).first()
			
			if sms_otp and not sms_otp.is_expired():
				# Valid SMS OTP
				sms_otp.is_used = True
				sms_otp.save()
				
				# Reset password
				user.set_password(new_password)
				user.save()
				
				return Response({
					'message': 'Password reset successful via SMS OTP. Please login with your new password.',
					'data': None
				}, status=status.HTTP_200_OK)
			
			# Check Google Authenticator TOTP
			if profile.is_2fa_enabled and profile.totp_secret:
				import pyotp
				totp = pyotp.TOTP(profile.totp_secret)
				
				if totp.verify(otp_code) and profile.last_otp_used != otp_code:
					# Valid TOTP and not reused
					profile.last_otp_used = otp_code
					profile.save()
					
					# Reset password
					user.set_password(new_password)
					user.save()
					
					return Response({
						'message': 'Password reset successful via Google Authenticator. Please login with your new password.',
						'data': None
					}, status=status.HTTP_200_OK)
			
			return Response({
				'message': 'Invalid or expired OTP',
				'data': None
			}, status=status.HTTP_400_BAD_REQUEST)
			
		except User.DoesNotExist:
			return Response({
				'message': 'Invalid OTP',
				'data': None
			}, status=status.HTTP_400_BAD_REQUEST)
		except ImportError:
			return Response({
				'message': 'Google Authenticator not properly configured',
				'data': None
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
	tags=["2FA"],
	summary="Enable 2FA (Google Authenticator)",
	description="""Enable Google Authenticator for the logged-in user.
	
	Returns QR code URL for easy setup in Google Authenticator app.
	Also generates backup codes for emergency access.
	"""
)
class Enable2FAView(generics.GenericAPIView):
	permission_classes = [IsAuthenticated]
	
	def post(self, request):
		try:
			import pyotp
			import qrcode
			from io import BytesIO
			import base64
			
			user = request.user
			profile = user.profile
			
			# Generate TOTP secret
			secret = pyotp.random_base32()
			
			# Create TOTP object
			totp = pyotp.TOTP(secret)
			
			# Generate QR code URL
			qr_url = totp.provisioning_uri(
				name=user.email,
				issuer_name="United Fins Inventory"
			)
			
			# Generate backup codes
			backup_codes = [
				''.join([str(random.randint(0, 9)) for _ in range(8)])
				for _ in range(10)
			]
			
			# Save to profile (don't enable yet - wait for verification)
			profile.totp_secret = secret
			profile.otp_backup_codes = backup_codes
			profile.save()
			
			return Response({
				'message': '2FA setup initialized. Scan QR code with Google Authenticator and verify.',
				'data': {
					'qr_code_url': qr_url,
					'secret_key': secret,
					'backup_codes': backup_codes,
					'setup_instructions': [
						"1. Install Google Authenticator app",
						"2. Scan the QR code or enter the secret key manually",
						"3. Enter the 6-digit code to verify setup",
						"4. Save backup codes in a secure place"
					]
				}
			}, status=status.HTTP_200_OK)
			
		except ImportError:
			return Response({
				'message': 'Please install pyotp library: pip install pyotp',
				'data': None
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
	tags=["2FA"],
	summary="Verify and Complete 2FA Setup",
	description="""Verify Google Authenticator setup by entering 6-digit code.
	
	This completes the 2FA setup and enables 2FA for the user.
	"""
)
class Verify2FASetupView(generics.GenericAPIView):
	permission_classes = [IsAuthenticated]
	
	class Verify2FASerializer(serializers.Serializer):
		totp_code = serializers.CharField(min_length=6, max_length=6)
		
	serializer_class = Verify2FASerializer
	
	def post(self, request):
		try:
			import pyotp
			
			serializer = self.get_serializer(data=request.data)
			serializer.is_valid(raise_exception=True)
			
			totp_code = serializer.validated_data['totp_code']
			user = request.user
			profile = user.profile
			
			if not profile.totp_secret:
				return Response({
					'message': 'No 2FA setup in progress. Please initialize 2FA setup first.',
					'data': None
				}, status=status.HTTP_400_BAD_REQUEST)
			
			# Verify TOTP code
			totp = pyotp.TOTP(profile.totp_secret)
			
			if totp.verify(totp_code):
				# Enable 2FA
				profile.is_2fa_enabled = True
				profile.save()
				
				return Response({
					'message': '2FA enabled successfully! Your account is now protected with two-factor authentication.',
					'data': {
						'backup_codes_count': len(profile.otp_backup_codes),
						'reminder': 'Save your backup codes in a secure place'
					}
				}, status=status.HTTP_200_OK)
			else:
				return Response({
					'message': 'Invalid verification code. Please try again.',
					'data': None
				}, status=status.HTTP_400_BAD_REQUEST)
				
		except ImportError:
			return Response({
				'message': 'Google Authenticator not properly configured',
				'data': None
			}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
