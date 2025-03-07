"""Views for the user API."""

from core.models import User
from rest_framework import generics, permissions

from user.serializers import UserSerializer


class ManageUserView(generics.RetrieveUpdateAPIView[User]):
    """Manage the authenticated user."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self) -> User:
        """Retrieves and returns the authenticated user.

        :return: User object if user is authenticated.
        """
        return self.request.user  # type: ignore
