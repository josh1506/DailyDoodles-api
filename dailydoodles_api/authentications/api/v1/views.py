from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from drf_spectacular.contrib.rest_framework_simplejwt import SimpleJWTScheme
from drf_spectacular.utils import extend_schema_serializer
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from dailydoodles_api.authentications.api.v1.serializers import UserRegistrationSerializer
from dailydoodles_api.authentications.api.v1.session_binding import SESSION_CLAIM, session_hash, token_matches_user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token["email"] = user.email
        token[SESSION_CLAIM] = session_hash(user)  # F1: invalidated by password change

        return token


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class UserRegistrationView(CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class ThrottledObtainAuthToken(ObtainAuthToken):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


@extend_schema_serializer(component_name="TokenRefresh")  # keep the published schema name
class SessionBoundTokenRefreshSerializer(TokenRefreshSerializer):
    # Refresh only while the token still matches the account (see session_binding, threat model F1).
    def validate(self, attrs):
        token = self.token_class(attrs["refresh"])  # signature, expiry and blacklist checks
        user = (
            get_user_model()
            .objects.filter(**{api_settings.USER_ID_FIELD: token.get(api_settings.USER_ID_CLAIM)})
            .first()
        )
        if user is None or not token_matches_user(token, user):
            raise InvalidToken(_("Token is no longer valid for this account."))
        return super().validate(attrs)


class SessionBoundTokenRefreshView(TokenRefreshView):
    serializer_class = SessionBoundTokenRefreshSerializer


class SessionBoundJWTScheme(SimpleJWTScheme):
    # Document SessionBoundJWTAuthentication exactly like simplejwt's Bearer scheme ("jwtAuth").
    target_class = "dailydoodles_api.authentications.api.v1.session_binding.SessionBoundJWTAuthentication"
