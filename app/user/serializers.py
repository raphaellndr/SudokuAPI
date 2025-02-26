"""Serializers for the user API View."""

from typing import TypedDict

from core.models import User
from django.contrib.auth import get_user_model
from rest_framework import serializers


class UserParams(TypedDict):
    """User parameters."""

    username: str
    email: str
    password: str


class UserSerializer(serializers.ModelSerializer[User]):
    """Serializer for the user object."""

    class Meta:
        """Meta class for the user serializer."""

        model = get_user_model()
        fields = ["email", "password", "username", "date_joined"]
        extra_kwargs = {"password": {"write_only": True, "min_length": 5}}

    def create(self, validated_data: UserParams) -> User:
        """Creates and returns a user with encrypted password.

        :param validated_data: User data.
        :return: User object.
        """
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance: User, validated_data: UserParams) -> User:
        """Updates and returns user.

        :param instance: User object.
        :param validated_data: User data.
        :return: Updated user object.
        """
        validated_data_copy = dict(validated_data)
        password = validated_data_copy.pop("password", None)
        user: User = super().update(instance, validated_data_copy)

        if password:
            user.set_password(password)  # type: ignore
            user.save()

        return user
