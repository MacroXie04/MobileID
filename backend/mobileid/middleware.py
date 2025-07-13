from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.urls import reverse

User = get_user_model()


class UserStatusMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # check if user is authenticated and not active
        if request.user.is_authenticated and not request.user.is_active:
            # exclude some urls from redirecting
            excluded_urls = [
                "/logout/",
                "/admin/",
                "/account-disabled/",
            ]

            # check if current url is in excluded urls
            current_path = request.path
            if not any(current_path.startswith(url) for url in excluded_urls):
                # redirect to account disabled page
                return redirect("mobileid:account_disabled")

        response = self.get_response(request)
        return response
