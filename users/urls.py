from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserRegistrationView, AdminRegistrationView, LogoutView, MeView, UserViewSet, 
    EmailTokenObtainPairView,
    RequestPasswordResetOTPView, VerifyOTPResetPasswordView, Enable2FAView, Verify2FASetupView
)

from rest_framework_simplejwt.views import TokenObtainPairView
from .views import CustomTokenRefreshView


from rest_framework.routers import SimpleRouter

# Use a router that supports UUIDs in the path
router = SimpleRouter()
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    path('register/admin/', AdminRegistrationView.as_view(), name='admin-register'),  # Public admin registration
    path('register/', UserRegistrationView.as_view(), name='user-register'),  # Protected user registration (admin only)
    path('login/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),
    
    # 2FA password reset (secure mode)
    path('request-otp-reset/', RequestPasswordResetOTPView.as_view(), name='request-otp-reset'),
    path('verify-otp-reset/', VerifyOTPResetPasswordView.as_view(), name='verify-otp-reset'),
    
    # 2FA setup
    path('enable-2fa/', Enable2FAView.as_view(), name='enable-2fa'),
    path('verify-2fa-setup/', Verify2FASetupView.as_view(), name='verify-2fa-setup'),
    
    path('', include(router.urls)),
]
