from django.urls import path

from authn.views import (webauthn, index)

app_name = "authn"

urlpatterns = []

# if API_SERVER:
#     urlpatterns += [
#     ]
#
# else:
urlpatterns += [
    # staff index page
    path("", index.staff_index, name="web_staff_index"),

    # webauthn
    path("login/", webauthn.web_login, name="web_login"),
    path("logout/", webauthn.web_logout, name="web_logout"),
    path("register/", webauthn.web_register, name="web_register"),

]
