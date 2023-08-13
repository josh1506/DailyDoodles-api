from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from dailydoodles_api.authentications.api.v1.views import CustomTokenObtainPairView, UserRegistrationView

urlpatterns = [
    path("token", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    path("register", UserRegistrationView.as_view(), name="register"),
]
