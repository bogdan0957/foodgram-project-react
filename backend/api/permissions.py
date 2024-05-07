from rest_framework.permissions import BasePermission

class IsAuthorOrAuthOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        if request.method == 'POST':
            return request.user.is_authenticated
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in ('PATCH', 'DELETE'):
            return request.user.is_authenticated and request.user == obj.author
        if request.method == 'GET':
            return True

        return False