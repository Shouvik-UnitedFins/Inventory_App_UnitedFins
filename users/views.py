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

from drf_spectacular.utils import extend_schema, extend_schema_view

@extend_schema_view(
	list=extend_schema(summary="List all users", tags=["Users"]),
	retrieve=extend_schema(summary="Retrieve a user", tags=["Users"]),
	update=extend_schema(summary="Update a user", tags=["Users"]),
	partial_update=extend_schema(summary="Partially update a user", tags=["Users"]),
	set_status=extend_schema(summary="Update user status", tags=["Users"]),
	set_password=extend_schema(summary="Set user password", tags=["Users"]),
)
class UserViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
	"""API endpoints for managing users."""

	from django.contrib.auth import get_user_model
	queryset = get_user_model().objects.all()
	serializer_class = UserDetailSerializer
	permission_classes = [IsAuthenticated]
	lookup_field = 'id'

	def get_queryset(self):
		"""Filter users based on role query parameter and user permissions"""
		queryset = super().get_queryset()
		
		# Filter by role query parameter
		role = self.request.query_params.get('role')
		if role:
			queryset = queryset.filter(profile__role=role)
		
		# Permission-based filtering
		current_user = self.request.user
		if hasattr(current_user, 'profile'):
			current_role = current_user.profile.role
			
			# Super admins can see all users
			if current_role == 'super_admin':
				return queryset
			
			# Admins can see all except super admins
			elif current_role == 'admin':
				return queryset.exclude(profile__role='super_admin')
			
			# Others can only see themselves
			else:
				return queryset.filter(id=current_user.id)
		
		# If no profile, only show themselves
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
		response = super().retrieve(request, *args, **kwargs)
		return Response({
			'message': 'User fetched successfully',
			'data': response.data
		}, status=response.status_code)

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
		user = self.get_object()
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		user.set_password(serializer.validated_data['password'])
		user.save()
		return Response({'message': 'Password set successfully'})
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

@extend_schema(tags=["Auth"])
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
