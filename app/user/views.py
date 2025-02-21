"""Views for the user API."""

from core.models import User
from rest_framework import authentication
from rest_framework import generics
from rest_framework import permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings

from user.serializers import AuthTokenSerializer
from user.serializers import UserSerializer


class CreateUserView(generics.CreateAPIView[User]):
    """Creates a new user in the system."""

    serializer_class = UserSerializer


class CreateTokenView(ObtainAuthToken):
    """Creates a new auth token for user."""

    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES  # type: ignore


class ManageUserView(generics.RetrieveUpdateAPIView[User]):
    """Manage the authenticated user."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self) -> User:
        """Retrieves and returns the authenticated user.

        :return: User object if user is authenticated.
        """
        return self.request.user  # type: ignore
