from rest_framework_simplejwt.tokens import RefreshToken


def authorize(self, user_obj):
    """Authorizes user_obj in APITestCase."""
    refresh = RefreshToken.for_user(user_obj)
    self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")


def authorize_fn(cls):
    """Add authorize function to a test class."""
    setattr(cls, "authorize", authorize)
    return cls