from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.conf import settings


# Custom user manager
class CustomUserManager(BaseUserManager):
	def create_user(self, email, password=None, **extra_fields):
		if not email:
			raise ValueError('The Email field must be set')
		email = self.normalize_email(email)
		user = self.model(email=email, **extra_fields)
		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_superuser(self, email, password=None, **extra_fields):
		extra_fields.setdefault('is_staff', True)
		extra_fields.setdefault('is_superuser', True)
		return self.create_user(email, password, **extra_fields)

# Custom user model
class User(AbstractBaseUser, PermissionsMixin):
	email = models.EmailField(unique=True)
	is_active = models.BooleanField(default=True)
	is_staff = models.BooleanField(default=False)
	date_joined = models.DateTimeField(auto_now_add=True)

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = []

	objects = CustomUserManager()

	def __str__(self):
		return self.email


# UserProfile model should be separate

class UserProfile(models.Model):
	ROLE_CHOICES = [
		("super_admin", "Super Admin"),
		("admin", "Admin"),
		("storekeeper", "Store Keeper"),
		("inventorymanager", "Inventory Manager"),
		("requester", "Requester"),
		("vendor", "Vendor"),
	]

	import uuid
	uuid = models.UUIDField(default=uuid.uuid4, editable=False)
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
	role = models.CharField(max_length=20, choices=ROLE_CHOICES)
	name = models.CharField(max_length=100, blank=True)
	phone_number = models.CharField(max_length=20, blank=True)
	latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
	longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
	blocked = models.BooleanField(default=False)
	
	# Two-Factor Authentication fields
	is_2fa_enabled = models.BooleanField(default=False, help_text="Whether 2FA is enabled for this user")
	totp_secret = models.CharField(max_length=32, blank=True, null=True, help_text="TOTP secret for Google Authenticator")
	last_otp_used = models.CharField(max_length=6, blank=True, null=True, help_text="Last used OTP to prevent replay attacks")
	otp_backup_codes = models.JSONField(default=list, blank=True, help_text="Backup codes for 2FA recovery")

	def __str__(self):
		return f"{self.user.email} ({self.get_role_display()})"


# OTP Model for SMS-based 2FA
class PasswordResetOTP(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	otp_code = models.CharField(max_length=6)
	is_used = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	expires_at = models.DateTimeField()
	request_type = models.CharField(max_length=20, choices=[
		('password_reset', 'Password Reset'),
		('login_verification', 'Login Verification'),
	], default='password_reset')
	
	class Meta:
		ordering = ['-created_at']
	
	def __str__(self):
		return f"OTP for {self.user.email} - {self.otp_code} ({'Used' if self.is_used else 'Active'})"
	
	def is_expired(self):
		from django.utils import timezone
		return timezone.now() > self.expires_at
	
	@classmethod
	def generate_otp(cls):
		import random
		return str(random.randint(100000, 999999))
