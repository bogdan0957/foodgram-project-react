from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminUserOrReadOnly(BasePermission):
    """Ограничение для доступа админа и авторизованного пользователя, остальные
    только для чтения"""

    def has_permission(self, request, view):
        return (request.method in SAFE_METHODS
                or request.user.is_authenticated and request.user.is_admin)


class IsAuthorAdminSuperuserOrReadOnlyPermission(BasePermission):
    """Ограничение для доступа автора админа и выше, остальные только для
    чтения"""

    message = (
        'Проверка пользователя является ли он администрацией'
        'или автором объекта, иначе только режим чтения'
    )

    def has_object_permission(self, request, view, obj):
        return (request.method in SAFE_METHODS
                or (request.user.is_admin
                    or request.user.is_moderator
                    or obj.author == request.user))


class IsAdminPermission(BasePermission):
    """Ограничение для доступа авторизованных админа и выше."""

    def has_permission(self, request, view):
        return (request.user.is_authenticated
                and request.user.is_admin)