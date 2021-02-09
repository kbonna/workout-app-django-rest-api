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


class IsHimself(permissions.BasePermission):
    """
    Object-level permission for User class allowing only user to interact with their own data.
    Assumes the model is an User instance.
    """

    def has_object_permission(self, request, view, obj):
        # Instance must be the user making request.
        return obj == request.user
