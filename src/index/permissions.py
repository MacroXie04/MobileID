from rest_framework.permissions import BasePermission


class IsNotUserGroup(BasePermission):
    """
    Denies access to users in the 'User' group.
    Caches group membership on the request to avoid repeated DB queries.
    """

    message = "User type accounts cannot access barcode dashboard"

    def has_permission(self, request, view):
        user_groups = _get_cached_groups(request)
        return "User" not in user_groups


class IsSchoolGroup(BasePermission):
    """
    Only allows access to users in the 'School' group.
    """

    message = "Only School group users can access this endpoint"

    def has_permission(self, request, view):
        user_groups = _get_cached_groups(request)
        return "School" in user_groups


def _get_cached_groups(request):
    """
    Fetch and cache user group names on the request object.
    Subsequent calls within the same request return the cached set.
    """
    if not hasattr(request, "_cached_user_groups"):
        request._cached_user_groups = set(
            request.user.groups.values_list("name", flat=True)
        )
    return request._cached_user_groups
