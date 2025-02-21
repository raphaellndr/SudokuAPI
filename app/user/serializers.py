"""Serializers for the user API View."""

from typing import Any
from typing import TypedDict

from core.models import User
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from rest_framework import serializers


class UserParams(TypedDict):
    """User parameters."""

    email: str
    password: str
    name: str


class UserSerializer(serializers.ModelSerializer[User]):
    """Serializer for the user object."""

    class Meta:
        """Meta class for the user serializer."""

        model = get_user_model()
        fields = ["email", "password", "name", "date_joined"]
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


class AuthTokenSerializer(serializers.Serializer[User]):
    """Serializer for the user auth token."""

    email = serializers.EmailField()
    password = serializers.CharField(
        style={"input_type": "password"},
        trim_whitespace=False,
    )

    def validate(self, attrs: Any) -> Any:
        """Validates and authenticates the user.

        :param attrs: User attributes.
        :return: User attributes.
        """
        email = attrs["email"]
        password = attrs["password"]
        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password,
        )
        if not user:
            msg = _("Unable to authenticate with provided credentials.")
            raise serializers.ValidationError(msg, code="authorization")

        attrs["user"] = user
        return attrs
