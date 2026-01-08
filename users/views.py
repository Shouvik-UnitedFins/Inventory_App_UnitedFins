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
		"""Block a user by email or name (admin/super_admin only)."""
		current_user = request.user
		if not hasattr(current_user, 'profile') or current_user.profile.role not in ['admin', 'super_admin']:
			return Response({'message': 'You do not have permission to block users.', 'data': None}, status=status.HTTP_403_FORBIDDEN)
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
		"""Unblock a user by email or name (admin/super_admin only)."""
		current_user = request.user
		if not hasattr(current_user, 'profile') or current_user.profile.role not in ['admin', 'super_admin']:
			return Response({'message': 'You do not have permission to unblock users.', 'data': None}, status=status.HTTP_403_FORBIDDEN)
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
			if current_role == 'super_admin':
				return queryset
			elif current_role == 'admin':
				return queryset.exclude(profile__role='super_admin')
			else:
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
			
			if not hasattr(current_user, 'profile') or current_user.profile.role not in ['admin', 'super_admin']:
				return Response({
					'message': 'You do not have permission to set passwords for other users. Only admins can perform this action.',
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
from django.contrib.auth.models import User
from .models import UserProfile
from .serializers import UserRegistrationSerializer

class IsAdminUserCustom(permissions.BasePermission):
	       def has_permission(self, request, view):
		       return (
			   request.user.is_authenticated and 
			   hasattr(request.user, 'profile') and 
			   request.user.profile.role in ['admin', 'super_admin']
		       )

@extend_schema(tags=["Auth"])
class UserRegistrationView(generics.CreateAPIView):
	from django.contrib.auth import get_user_model
	queryset = get_user_model().objects.all()
	serializer_class = UserRegistrationSerializer
	permission_classes = [IsAdminUserCustom]

	def create(self, request, *args, **kwargs):
		response = super().create(request, *args, **kwargs)
		if response.status_code == 201:
			return Response({
				'message': 'Registration successful',
				'data': response.data
			}, status=response.status_code)
		return response
