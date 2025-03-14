"""Serializers for the user API View."""

from typing import TypedDict

from rest_framework import serializers

from .models import User


class UserParams(TypedDict):
    """User parameters."""

    username: str
    email: str
    password: str


class UserSerializer(serializers.ModelSerializer[User]):
    """`User` serializer."""

    class Meta:
        """Meta class for the User serializer."""

        model = User
        fields = ["email", "password", "username"]
        extra_kwargs = {"password": {"write_only": True, "min_length": 5}}

    def create(self, validated_data: UserParams) -> User:
        """Creates and returns a user with encrypted password.

        :param validated_data: User data.
        :return: `User` object.
        """
        user = User(
            username=validated_data["username"],
            email=validated_data["email"],
        )
        user.set_password(validated_data["password"])
        user.save()
        return user

    def update(self, instance: User, validated_data: UserParams) -> User:
        """Updates and returns the `User`.

        :param instance: `User` object.
        :param validated_data: `User` data.
        :return: Updated `User` object.
        """
        validated_data_copy = dict(validated_data)
        password = validated_data_copy.pop("password", None)
        user: User = super().update(instance, validated_data_copy)

        if password:
            user.set_password(password)  # type: ignore
            user.save()

        return user
