from rest_framework import permissions
from shared_models.models import Permission, CustomRole


class HasRoleBasedPermission(permissions.BasePermission):
    """
    Global permission class to check if a user has access to the operation.
    """

    message = 'This action in this model is not allowed for this user'

    def has_permission(self, request, view):
        operation = view.__class__.__name__

        if request.user.is_superuser or request.user.is_scope_disabled:
            return True

        if operation in ['MFAActivateView', 'MFADeactivateView']:
            return True

        permission_ids = []
        action = ''
        custom_roles = CustomRole.objects.filter(id__in=request.user.custom_roles)

        for role in custom_roles:
            permission_ids = permission_ids + role.permissions

        operation = view.__class__.__name__
        if request.method == 'GET':
            action = 'r'

        if request.method in ['POST', 'PUT', 'PATCH']:
            action = 'w'

        if request.method == 'DELETE':
            action = 'd'

        return Permission.objects.filter(id__in=permission_ids, operation=operation, action=action).exists()
