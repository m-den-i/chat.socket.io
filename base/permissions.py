from rest_framework import permissions


class IsSelf(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            obj == request.user
        )


class IsSelfOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return(
            request.method in permissions.SAFE_METHODS or
            obj == request.user
        )


class UserIsAuthenticated(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated()


class POSTOnlyIfAnonymous(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated() or request.method in ['POST']
        )
