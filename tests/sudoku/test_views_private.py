"""Test the Sudoku views for an authenticated user."""

from typing import Final

import pytest
from core.models import Sudoku
from django.urls import reverse
from rest_framework import status
from sudoku.serializers import SudokuSerializer

SUDOKUS_URL: Final[str] = reverse("sudoku:sudoku-list")


@pytest.fixture
def set_up(api_client, create_user, user_payload):
    """Sets up a client for authenticated tests."""
    user = create_user(**user_payload)
    client = api_client(user=user)
    return client, user


def test_create_sudoku(set_up, sudoku_payload) -> None:
    """Tests creating a sudoku is successful when authenticated."""
    client, user = set_up

    response = client.post(SUDOKUS_URL, sudoku_payload)
    assert response.status_code == status.HTTP_201_CREATED

    sudoku = Sudoku.objects.get(id=response.data["id"])
    for k, v in sudoku_payload.items():
        assert getattr(sudoku, k) == v
    assert sudoku.user == user


@pytest.mark.parametrize(
    "limit,offset,expected_count",
    [
        (None, None, 5),  # default limit is 5
        (5, None, 5),  # if not offset, fetches first 5 items (same as default)
        (10, None, 10),  # if limit is 10, fetches every item
        (None, 5, 5),  # if no limit and offset is 5, fetches the last 5 items
        (None, 10, 0),  # if offset if 10, fetches no items since 10 are created
        (5, 7, 3),  # if offset 7, fetches the last 3 items
        (None, -3, 5),  # if offset is negative, fetches the first 5 items
    ],
)
def test_retrieve_sudokus(
    set_up, create_sudokus, limit: int | None, offset: int | None, expected_count: int
) -> None:
    """Tests that retrieving a list of sudokus is successful for an authenticated user."""
    client, user = set_up
    create_sudokus(user=user)

    params: dict[str, int] = {}
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset

    response = client.get(SUDOKUS_URL, params)
    assert response.status_code == status.HTTP_200_OK

    assert len(response.data["results"]) == expected_count
    if offset is None or offset < 0:
        offset = 0
    expected_sudokus = Sudoku.objects.filter(user=user).order_by("-id")[
        offset : expected_count + offset
    ]
    serializer = SudokuSerializer(expected_sudokus, many=True)
    assert response.data["results"] == serializer.data


def test_sudoku_list_limited_to_auth_user(
    set_up, create_user, create_sudoku, create_sudokus
) -> None:
    """Tests that retrieving a list of sudokus is limited to authenticated user."""
    client, user = set_up
    other_user = create_user()

    create_sudoku(user=user)
    create_sudokus(size=3, user=other_user)

    response = client.get(SUDOKUS_URL)
    assert response.status_code == status.HTTP_200_OK

    sudokus = Sudoku.objects.filter(user=user)
    assert len(sudokus) == 1
    serializer = SudokuSerializer(sudokus, many=True)
    assert response.data["results"] == serializer.data


def test_partially_update_sudoku(set_up, create_sudoku, sudoku_payload) -> None:
    """Tests partially updating a sudoku is successful when authenticated."""
    client, user = set_up
    sudoku = create_sudoku(user=user)

    response = client.patch(f"{SUDOKUS_URL}{sudoku.id}/", {"title": sudoku_payload["title"]})

    assert response.status_code == status.HTTP_200_OK
    sudoku.refresh_from_db()
    assert sudoku.title == sudoku_payload["title"]
    assert sudoku.user == user


def test_fully_update_sudoku(set_up, create_sudoku, sudoku_payload) -> None:
    """Tests fully updating a sudoku is successful when authenticated."""
    client, user = set_up
    sudoku = create_sudoku(user=user)

    response = client.put(f"{SUDOKUS_URL}{sudoku.id}/", sudoku_payload)

    assert response.status_code == status.HTTP_200_OK
    sudoku.refresh_from_db()
    for k, v in sudoku_payload.items():
        assert getattr(sudoku, k) == v
    assert sudoku.user == user


def test_update_user_does_not_work(set_up, create_user, create_sudoku) -> None:
    """Tests that changing the sudoku's user does not work."""
    client, user = set_up
    new_user = create_user()
    sudoku = create_sudoku(user=user)

    payload = {"user": new_user.id}
    response = client.patch(f"{SUDOKUS_URL}{sudoku.id}/", payload)
    assert response.status_code == status.HTTP_200_OK

    sudoku.refresh_from_db()
    assert sudoku.user == user


def test_delete_sudoku(set_up, create_sudoku) -> None:
    """Tests deleting a sudoku is successful when authenticated."""
    client, user = set_up
    sudoku = create_sudoku(user=user)

    response = client.delete(f"{SUDOKUS_URL}{sudoku.id}/")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    with pytest.raises(Sudoku.DoesNotExist):
        Sudoku.objects.get(id=sudoku.id)


def test_delete_sudoku_does_not_work(set_up, create_user, create_sudoku) -> None:
    """Tests that deleting a sudoku that doesn't belong to the authenticated user does not work."""
    client, _ = set_up
    other_user = create_user()
    sudoku = create_sudoku(user=other_user)

    response = client.delete(f"{SUDOKUS_URL}{sudoku.id}/")
    assert response.status_code == status.HTTP_404_NOT_FOUND

    assert sudoku.user == other_user
    assert Sudoku.objects.filter(id=sudoku.id).exists()


@pytest.mark.parametrize(
    "difficulties,nb_sudokus",
    [
        ("Easy", 1),
        ("Medium", 1),
        ("Hard", 0),
        ("Easy,Medium", 2),
    ],
)
def test_filter_sudokus_by_difficulties(
    set_up, create_sudoku, difficulties: str, nb_sudokus: int
) -> None:
    """Tests filtering sudokus by difficulties."""
    client, user = set_up
    create_sudoku(user=user, difficulty="Easy")
    create_sudoku(user=user, difficulty="Medium")

    response = client.get(SUDOKUS_URL, {"difficulties": difficulties})

    assert response.status_code == status.HTTP_200_OK

    fetched_sudokus = response.data["results"]
    assert len(fetched_sudokus) == nb_sudokus
    if nb_sudokus > 0:
        for response_data in fetched_sudokus:
            sudoku_id = response_data["id"]
            sudoku = Sudoku.objects.get(id=sudoku_id)
            serializer = SudokuSerializer(sudoku)
            assert response_data == serializer.data
