from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """Каталог читают все, меняет только персонал."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Читать может любой, кому объект вообще выдан вьюхой,
    менять и удалять — только автор (персоналу тоже можно, для модерации).
    """

    owner_field = 'user'

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user and request.user.is_staff:
            return True
        return getattr(obj, self.owner_field, None) == request.user
