from rest_framework.permissions import BasePermission


class IsTeacherOrAdmin(BasePermission):

    def has_permission(self, request, view):

        user = request.user

        if not user or not user.is_authenticated:
            return False

        return user.role in ['teacher', 'admin']