from django.urls import path
from rest_framework_simplejwt.views import TokenBlacklistView

from dailydoodles_api.authentications.api.v1.views import (
    CustomTokenObtainPairView,
    SessionBoundTokenRefreshView,
    UserRegistrationView,
)

urlpatterns = [
    path("token", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh", SessionBoundTokenRefreshView.as_view(), name="token_refresh"),
    path("token/blacklist", TokenBlacklistView.as_view(), name="token_blacklist"),
    path("register", UserRegistrationView.as_view(), name="register"),
]
