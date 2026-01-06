from django.db import models
from django.contrib.auth.models import User

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
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
	role = models.CharField(max_length=20, choices=ROLE_CHOICES)

	def __str__(self):
		return f"{self.user.username} ({self.get_role_display()})"
