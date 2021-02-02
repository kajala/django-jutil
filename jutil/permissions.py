from rest_framework import permissions


class UserIsOwner(permissions.BasePermission):
    """
    Object-level permission to only allow authorized users of an object to edit it.
    Assumes the model instance has an `user` attribute (can be overriden with user_field).
    """

    user_field = "user"

    def has_object_permission(self, request, view, obj):
        if not hasattr(obj, self.user_field):
            raise Exception("UserIsOwner: obj.{} does not exist: {}".format(self.user_field, obj))
        u = request.user
        return u and u.is_authenticated and getattr(obj, self.user_field) == u


class IsSameUser(permissions.BasePermission):
    """
    Allow access to use only to user himself.
    """

    def has_object_permission(self, request, view, obj):
        u = request.user
        return u and u.is_authenticated and obj.id == u.id
