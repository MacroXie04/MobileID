from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render
from django.urls import reverse

User = get_user_model()

class AccountTypeRoutingMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Handle staff access restrictions
        if request.user.is_authenticated:
            try:
                user_account_type = request.user.useraccount.account_type
                
                # Block staff users from accessing generate_barcode and barcode_dashboard
                if user_account_type == "Staff":
                    restricted_paths = ["/generate_barcode/", "/barcode_dashboard/"]
                    if request.path in restricted_paths:
                        from django.http import HttpResponseForbidden
                        return HttpResponseForbidden("Staff users are not allowed to access this page")
            except Exception as e:
                # if any exception occurs, continue normal processing flow
                pass
        
        # only handle root path
        if request.path == "/" and request.user.is_authenticated:
            try:
                # check if user has UserProfile
                from mobileid.models import UserProfile
                try:
                    info = UserProfile.objects.get(user=request.user)
                except UserProfile.DoesNotExist:
                    return redirect("mobileid:web_edit_profile")

                # get user account type
                user_account_type = request.user.useraccount.account_type

                # prepare template context
                context = {
                    "name": info.name,
                    "information_id": info.information_id,
                    "user_profile_img": info.user_profile_img,
                }

                # render different templates based on account type
                if user_account_type == "School":
                    return render(request, "index/index.html", context)
                elif user_account_type == "User":
                    return render(request, "index/index_user.html", context)
                elif user_account_type == "Staff":
                    return render(request, "index/index_staff.html", context)
                else:
                    # unknown account type, return 404
                    from django.http import Http404
                    raise Http404("Unknown account type")

            except Exception as e:
                # if any exception occurs, continue normal processing flow
                pass

        response = self.get_response(request)
        return response
