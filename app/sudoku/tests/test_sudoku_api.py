"""Tests for the sudoku API."""

from typing import Any
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Sudoku
from sudoku.serializers import SudokuSerializer

SUDOKUS_URL = reverse("sudoku:sudoku-list")


def create_user(**params: Any) -> AbstractUser:
    """Creates and returns a new user.

    :param params: User parameters.
    :return: User object.
    """
    return get_user_model().objects.create_user(**params)


def detail_url(sudoku_id: int) -> str:
    """Creates and returns a sudoku detail URL.

    :param sudoku_id: Sudoku ID.
    :return: Sudoku detail URL.
    """
    return reverse("sudoku:sudoku-detail", args=[sudoku_id])


def create_sudoku(user, **params: dict[str, str]) -> Sudoku:
    """Creates and returns a sample sudoku.

    :param user: User object.
    :param params: Sudoku parameters.
    :return: Sudoku object.
    """
    defaults = {
        "title": "Sample sudoku title.",
        "difficulty": "UNKNOWN",
        "grid": "." * 81,
    }
    defaults.update(params)

    sudoku = Sudoku.objects.create(user=user, **defaults)
    return sudoku


class PublicSudokuAPITests(TestCase):
    """Tests unauthenticated API requests."""

    def setUp(self) -> None:
        """Sets up tests."""
        self.client = APIClient()

    def test_auth_required(self) -> None:
        """Tests auth is required to call API."""
        res = self.client.get(SUDOKUS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateSudokuAPITests(TestCase):
    """Tests authenticated API requests."""

    def setUp(self) -> None:
        """Sets up tests."""
        self.user = create_user(email="test@example.com", password="test123")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def retreive_sudokus(self) -> None:
        """Tests retreiving a list of sudokus."""
        create_sudoku(user=self.user)
        create_sudoku(user=self.user)

        res = self.client.get(SUDOKUS_URL)

        sudokus = Sudoku.objects.all().order_by("-id")
        serializer = SudokuSerializer(sudokus, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_sudoku_list_limited_to_auth_user(self) -> None:
        """Tests list of sudokus is limited to authenticated user."""
        other_user = create_user(email="other@example.com", password="test123")
        create_sudoku(user=other_user)
        create_sudoku(user=self.user)

        res = self.client.get(SUDOKUS_URL)

        recipes = Sudoku.objects.filter(user=self.user)
        serializer = SudokuSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_sudoku(self) -> None:
        """Tests creating a sudoku."""
        payload = {
            "title": "Sample sudoku title.",
            "difficulty": "UNKNOWN",
            "grid": "." * 81,
        }
        res = self.client.post(SUDOKUS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        sudoku = Sudoku.objects.get(id=res.data["id"])
        for k, v in payload.items():
            self.assertEqual(getattr(sudoku, k), v)
        self.assertEqual(sudoku.user, self.user)

    def test_partial_update(self) -> None:
        """Tests a partial update of a sudoku."""
        original_title = "Sample sudoku title"
        sudoku = create_sudoku(
            user=self.user,
            title=original_title,
            grid="." * 81,
        )

        payload = {"grid": "9" + "." * 80}
        url = detail_url(sudoku.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        sudoku.refresh_from_db()
        self.assertEqual(sudoku.title, original_title)
        self.assertEqual(sudoku.grid, payload["grid"])
        self.assertEqual(sudoku.user, self.user)

    def test_full_update(self) -> None:
        """Tests full update of a sudoku."""
        sudoku = create_sudoku(self.user)
        payload = {
            "title": "Fully updated sudoku",
            "difficulty": "EASY",
            "grid": "9" * 81,
        }
        url = detail_url(sudoku.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        sudoku.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(sudoku, k), v)
        self.assertEqual(sudoku.user, self.user)

    def test_update_user_returns_error(self) -> None:
        """Tests changing the sudoku's user results in an error."""
        new_user = create_user(email="user2@example.com", password="123pass")
        recipe = create_sudoku(user=self.user)

        payload = {"user": new_user.id}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_sudoku(self) -> None:
        """Tests deleting a sudoku is successful."""
        sudoku = create_sudoku(user=self.user)

        url = detail_url(sudoku.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Sudoku.objects.filter(id=sudoku.id).exists())

    def test_delete_other_users_sudoku_error(self) -> None:
        """Tests trying to delete another user's sudoku gives an error."""
        new_user = create_user(email="other@example.com", password="pass123")
        sudoku = create_sudoku(user=new_user)

        url = detail_url(sudoku.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Sudoku.objects.filter(id=sudoku.id).exists())

    def test_filter_sudokus_by_difficulties(self) -> None:
        """Tests filtering sudokus by difficulties."""
        easy_sudoku = create_sudoku(user=self.user, difficulty="EASY")
        medium_sudoku = create_sudoku(user=self.user, difficulty="MEDIUM")

        res = self.client.get(SUDOKUS_URL, {"difficulties": "EASY"})

        # Filter by only one difficulty
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["title"], easy_sudoku.title)

        # Filter by multiple difficulties
        res = self.client.get(SUDOKUS_URL, {"difficulties": "EASY,MEDIUM"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
        titles = {sudoku["title"] for sudoku in res.data}
        self.assertIn(easy_sudoku.title, titles)
        self.assertIn(medium_sudoku.title, titles)
