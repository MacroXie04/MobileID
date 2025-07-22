from django.contrib.auth import get_user_model
from django.http import Http404
from django.shortcuts import redirect, render
from authn.models import UserProfile

User = get_user_model()


class AccountTypeRoutingMiddleware:
    # Publicly accessible paths (everyone can access)
    PUBLIC_PATHS = {"/authn/login/", "/authn/logout/", "/authn/register/"}

    # Pages User & School can access
    USER_ALLOWED_PATHS = {"/generate_barcode/", "/barcode_dashboard/", "/authn/edit_profile/"}

    # Pages Staff cannot access
    STAFF_RESTRICTED_PATHS = {"/generate_barcode/", "/barcode_dashboard/"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        user = request.user
        is_authenticated = user.is_authenticated

        # Allow public paths to everyone
        if path in self.PUBLIC_PATHS:
            return self.get_response(request)

        # Handle authenticated users
        if is_authenticated:
            # Force profile completion
            if path != "/edit_profile/":
                try:
                    UserProfile.objects.get(user=user)
                except UserProfile.DoesNotExist:
                    return redirect("authn:web_edit_profile")

            # Staff access restrictions
            if self.is_in_group(user, "Staff") and path in self.STAFF_RESTRICTED_PATHS:
                return redirect("authn:web_staff_index")

            # User/School allowed only to specific paths
            if self.is_in_group(user, "User") or self.is_in_group(user, "School"):
                if (
                    path not in self.USER_ALLOWED_PATHS
                    and path != "/"
                    and path not in self.PUBLIC_PATHS
                ):
                    raise Http404("User/School cannot access this page")

            # Root path "/" routing by group
            if path == "/":
                if self.is_in_group(user, "School"):
                    template = "index/index.html"
                elif self.is_in_group(user, "User"):
                    template = "index/index_user.html"
                elif self.is_in_group(user, "Staff"):
                    return redirect("authn:web_staff_index")
                else:
                    raise Http404("Unknown user group")

                profile = UserProfile.objects.get(user=user)
                context = {
                    "name": profile.name,
                    "information_id": profile.information_id,
                    "user_profile_img": profile.user_profile_img,
                }
                return render(request, template, context)

        # All other requests
        return self.get_response(request)

    @staticmethod
    def is_in_group(user, group_name):
        return user.groups.filter(name=group_name).exists()
