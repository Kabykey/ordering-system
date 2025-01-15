from rest_framework import  permissions

class IsAdminOrOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.role == 'Admin' or obj.customer_name == request.user.username