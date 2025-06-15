from django.contrib import admin
from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .views import index, manage_profile, generate_code, transfer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    return Response({'id': request.user.id, 'username': request.user.username})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/me/', current_user),

    # index page
    path("", index.index, name="index"),

    # manage profile
    path('setup/', manage_profile.setup, name='setup'),
    path('settings/', manage_profile.settings, name='settings'),

    # barcode generation
    path('generate_barcode/', generate_code.generate_code, name='generate_barcode'),

    # manage barcode
    path('transfer/', transfer.transfer_key, name='transfer'),
    path('create_barcode/', manage_profile.create_barcode, name='create_barcode'),
    path('manage_barcode/', manage_profile.manage_barcode, name='manage_barcode'),
]
