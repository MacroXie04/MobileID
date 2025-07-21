from django.contrib.auth import get_user_model
from django.http import Http404
from django.shortcuts import redirect, render
from authn.models import UserProfile

User = get_user_model()


class AccountTypeRoutingMiddleware:

    # Paths that Staff users are not allowed to visit
    RESTRICTED_FOR_STAFF = {"/generate_barcode/", "/barcode_dashboard/"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        is_authenticated = user.is_authenticated

        # ---------- 1) Block Staff users from restricted paths ----------
        if is_authenticated:
            account_type = getattr(getattr(user, "useraccount", None), "account_type", None)
            if account_type == "Staff" and request.path in self.RESTRICTED_FOR_STAFF:
                return redirect("authn:web_staff_index")

        # ---------- 2) Handle root path "/" ----------
        if request.path == "/" and is_authenticated:
            # a) Force users without a profile to complete it first
            try:
                profile = UserProfile.objects.get(user=user)
            except UserProfile.DoesNotExist:
                return redirect("authn:web_edit_profile")

            account_type = getattr(getattr(user, "useraccount", None), "account_type", None)

            # b) Route or redirect based on account_type
            if account_type == "School":
                template = "index/index.html"
            elif account_type == "User":
                template = "index/index_user.html"
            elif account_type == "Staff":
                return redirect("authn:web_staff_index")
            else:
                raise Http404("Unknown account type")

            context = {
                "name": profile.name,
                "information_id": profile.information_id,
                "user_profile_img": profile.user_profile_img,
            }
            return render(request, template, context)

        # ---------- 3) For all other requests, continue processing ----------
        return self.get_response(request)
