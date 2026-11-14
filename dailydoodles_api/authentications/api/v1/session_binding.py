"""Bind JWTs to the account's current credentials (threat model F1).

Every token carries a short HMAC of the user's password hash (Django's ``get_session_auth_hash``,
the same mechanism that logs out Django sessions on password change). Refresh and every
authenticated request re-check it, so changing or resetting the password, or deactivating the
account, immediately invalidates all of the user's access and refresh tokens. That includes
rotated refresh tokens, which simplejwt 5.3 doesn't record as outstanding and so can't be
blacklisted in bulk. No schema change, no DB writes.

Keep this module free of view imports: DRF imports it while loading rest_framework.views.
"""
from django.conf import settings
from django.utils.crypto import constant_time_compare
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

SESSION_CLAIM = "sah"


def session_hash(user) -> str:
    # 128 bits of an HMAC keyed with SECRET_KEY: safe to expose in a client-readable JWT.
    return user.get_session_auth_hash()[:32]


def token_matches_user(token, user) -> bool:
    if not user.is_active:
        return False
    claim = token.get(SESSION_CLAIM)
    if claim is None:
        # Tokens issued before this control existed. Rejected by default (one-time re-login after
        # deploy); DJANGO_JWT_REQUIRE_SESSION_CLAIM=False accepts them during a transition window.
        return not getattr(settings, "JWT_REQUIRE_SESSION_CLAIM", True)
    return constant_time_compare(claim, session_hash(user))


class SessionBoundJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if not token_matches_user(validated_token, user):
            raise InvalidToken("Token is no longer valid for this account.")
        return user
