from django.urls import path
from barcode.settings import (API_SERVER)
from mobileid.views import (barcode, index, manage)
from authn.views import change_info

app_name = "mobileid"

urlpatterns = []

if API_SERVER:
    urlpatterns += [
    ]


else:
    urlpatterns += [
        # index page
        path("", index.index, name="web_index"),

        # generate barcode
        path(
            "generate_barcode/",
            barcode.generate_barcode_view,
            name="web_generate_barcode",
        ),

        # edit profile
        path("edit_profile/", change_info.edit_profile, name="web_edit_profile"),

        # edit barcode settings
        path(
            "barcode_dashboard/",
            manage.barcode_dashboard,
            name="web_barcode_dashboard",
        ),
    ]

