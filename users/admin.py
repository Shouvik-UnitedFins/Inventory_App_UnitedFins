from django.contrib import admin
from .models import User

admin.site.register(User)
from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
	list_display = ("user", "role")
	list_filter = ("role",)
