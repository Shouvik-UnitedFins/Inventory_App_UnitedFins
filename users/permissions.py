from rest_framework import permissions

class IsAdminRole(permissions.BasePermission):
    """
    Custom permission to only allow users with admin role in their profile.
    This works with our UserProfile.role = 'admin' system instead of Django's is_staff.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and 
            request.user.profile.role == 'admin'
        )

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow read access to authenticated users,
    but only allow write access to admin role users.
    """
    
    def has_permission(self, request, view):
        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Write permissions only for admin role
        return (
            request.user and 
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and 
            request.user.profile.role == 'admin'
        )