from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from dailydoodles_api.authentications.api.v1.views import CustomTokenObtainPairView

urlpatterns = [
    path("", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
