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
		("store_keeper", "Store Keeper"),
		("inventory_manager", "Inventory Manager"),
		("requester", "Requester"),
		("vendor", "Vendor"),
	]
	import uuid
	uuid = models.UUIDField(default=uuid.uuid4, editable=False)
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
	role = models.CharField(max_length=20, choices=ROLE_CHOICES)

	def __str__(self):
		return f"{self.user.email} ({self.get_role_display()})"
