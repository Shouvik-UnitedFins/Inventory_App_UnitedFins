from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserRegistrationView, AdminRegistrationView, LogoutView, MeView, UserViewSet, EmailTokenObtainPairView

from rest_framework_simplejwt.views import TokenObtainPairView
from .views import CustomTokenRefreshView


from rest_framework.routers import SimpleRouter

# Use a router that supports UUIDs in the path
from rest_framework.routers import SimpleRouter
router = SimpleRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('register/admin/', AdminRegistrationView.as_view(), name='admin-register'),  # Public admin registration
    path('register/', UserRegistrationView.as_view(), name='user-register'),  # Protected user registration (admin only)
    path('login/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),
    path('', include(router.urls)),
]
