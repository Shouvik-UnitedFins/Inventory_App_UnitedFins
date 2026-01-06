from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from .serializers import UserDetailSerializer, UserUpdateSerializer, UserStatusSerializer, UserPasswordSerializer
# User management viewset (CRUD, status, password)
class UserViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
	queryset = User.objects.all()
	serializer_class = UserDetailSerializer
	permission_classes = [IsAuthenticated]

	def get_serializer_class(self):
		if self.action == 'update' or self.action == 'partial_update':
			return UserUpdateSerializer
		if self.action == 'set_status':
			return UserStatusSerializer
		if self.action == 'set_password':
			return UserPasswordSerializer
		return UserDetailSerializer

	def list(self, request, *args, **kwargs):
		return super().list(request, *args, **kwargs)

	def retrieve(self, request, *args, **kwargs):
		return super().retrieve(request, *args, **kwargs)

	def update(self, request, *args, **kwargs):
		return super().update(request, *args, **kwargs)

	def partial_update(self, request, *args, **kwargs):
		return super().partial_update(request, *args, **kwargs)

	@action(detail=True, methods=['patch'], url_path='status')
	def set_status(self, request, pk=None):
		user = self.get_object()
		serializer = self.get_serializer(user, data=request.data, partial=True)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		return Response({'status': 'updated'})

	@action(detail=True, methods=['patch'], url_path='password')
	def set_password(self, request, pk=None):
		user = self.get_object()
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		user.set_password(serializer.validated_data['password'])
		user.save()
		return Response({'status': 'password set'})
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User

# Logout API (blacklist refresh token)
class LogoutView(APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request):
		try:
			refresh_token = request.data["refresh"]
			token = RefreshToken(refresh_token)
			token.blacklist()
			return Response(status=status.HTTP_205_RESET_CONTENT)
		except Exception as e:
			return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# Get logged-in user API
class MeView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		user = request.user
		profile = getattr(user, 'profile', None)
		return Response({
			"id": user.id,
			"username": user.username,
			"email": user.email,
			"role": profile.role if profile else None,
		})
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import UserProfile
from .serializers import UserRegistrationSerializer

class IsAdminUserCustom(permissions.BasePermission):
	def has_permission(self, request, view):
		return request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.role == 'admin'

class UserRegistrationView(generics.CreateAPIView):
	queryset = User.objects.all()
	serializer_class = UserRegistrationSerializer
	permission_classes = [IsAdminUserCustom]

	def create(self, request, *args, **kwargs):
		return super().create(request, *args, **kwargs)
