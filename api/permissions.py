from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Instance must have an attribute named `owner`.
        return obj.owner == request.user


class IsUserOrReadOnly(permissions.BasePermission):
    """
    Object-level permission for User class allowing only user update only their own data. Safe
    methods are permitted for all users.

    Assumes the model is an User instance.
    """

    def has_object_permission(self, request, view, obj):
        # Instance must be the user making request.
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj == request.user


class IsHisResource(permissions.BasePermission):
    """
    View-level permission checking if requested resource is owned by a request author. It assumes
    that view contains user_pk in kwargs.

    Example:
        Endpoint /users/1/resource will be accessible only if request.user.pk is 1.
    """

    def has_permission(self, request, view):
        user_pk = view.kwargs.get("user_pk", None)
        if request.user.pk == user_pk:
            return True
        return False
