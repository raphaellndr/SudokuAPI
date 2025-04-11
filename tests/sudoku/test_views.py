"""Test the Sudoku views for both authenticated and anonymous users."""

from contextlib import nullcontext as does_not_raise

import pytest
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from sudoku.choices import SudokuDifficultyChoices, SudokuStatusChoices
from sudoku.models import Sudoku, SudokuSolution
from sudoku.serializers import SudokuSerializer
from sudoku.views import SudokuViewSet

from .urls import SUDOKUS_URL, solution_url, solver_url, status_url, sudoku_url


@pytest.mark.parametrize(
    "user",
    [
        "create_user",
        None,
    ],
)
def test_create_sudoku(request, api_client, sudoku_payload, user: str | None) -> None:
    """Tests creating a sudoku is successful when authenticated."""
    if user is not None:
        user = request.getfixturevalue(user)()
    client = api_client(user)

    response = client.post(SUDOKUS_URL, sudoku_payload)
    assert response.status_code == status.HTTP_201_CREATED

    sudoku = Sudoku.objects.get(id=response.data["id"])
    for k, v in sudoku_payload.items():
        assert getattr(sudoku, k) == v
    assert sudoku.user == user


@pytest.mark.parametrize(
    "user",
    [
        "create_user",
        None,
    ],
)
def test_retrieve_sudoku(request, api_client, create_sudoku, user: str | None) -> None:
    """Tests that retrieving a sudoku is successful."""
    if user is not None:
        user = request.getfixturevalue(user)()
    client = api_client(user)
    sudoku = create_sudoku(user=user)

    url = sudoku_url(sudoku.id)
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == str(sudoku.id)
    assert response.data["title"] == sudoku.title
    assert response.data["difficulty"] == sudoku.difficulty
    assert response.data["grid"] == sudoku.grid
    assert response.data["status"] == "created"


@pytest.mark.parametrize(
    "user",
    [
        "create_user",
        None,
    ],
)
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
    request,
    api_client,
    create_sudokus,
    user: str | None,
    limit: int | None,
    offset: int | None,
    expected_count: int,
) -> None:
    """Tests that retrieving a list of sudokus is successful for an authenticated user."""
    if user is not None:
        user = request.getfixturevalue(user)()
    client = api_client(user)
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
    expected_sudokus = Sudoku.objects.filter(user=user).order_by("-created_at")[
        offset : expected_count + offset
    ]
    serializer = SudokuSerializer(expected_sudokus, many=True)
    assert response.data["results"] == serializer.data


@pytest.mark.parametrize(
    "user",
    [
        "create_user",
        None,
    ],
)
def test_sudoku_list_limited_to_current_user(
    request, api_client, create_user, create_sudokus, user: str | None
) -> None:
    """Tests that retrieving a list of sudokus is limited to current user."""
    if user is not None:
        user = request.getfixturevalue(user)()
    client = api_client(user)
    other_user = create_user()

    create_sudokus(size=2, user=user)
    create_sudokus(size=3, user=other_user)

    response = client.get(SUDOKUS_URL)
    assert response.status_code == status.HTTP_200_OK

    sudokus = Sudoku.objects.filter(user=user).order_by("-created_at")
    assert len(sudokus) == 2
    serializer = SudokuSerializer(sudokus, many=True)
    assert response.data["results"] == serializer.data


@pytest.mark.parametrize(
    "user,status",
    [
        ("create_user", status.HTTP_200_OK),
        (None, status.HTTP_401_UNAUTHORIZED),
    ],
)
def test_partially_update_sudoku(
    request, api_client, create_sudoku, sudoku_payload, user: str | None, status: int
) -> None:
    """Tests partially updating a sudoku is successful only when authenticated."""
    if user is not None:
        user = request.getfixturevalue(user)()
    client = api_client(user)
    sudoku = create_sudoku(user=user)

    url = sudoku_url(sudoku.id)
    response = client.patch(url, {"title": sudoku_payload["title"]})

    assert response.status_code == status
    sudoku.refresh_from_db()
    if user is not None:
        assert sudoku.title == sudoku_payload["title"]
    else:
        assert sudoku.title == "sudoku title"
    assert sudoku.user == user


@pytest.mark.parametrize(
    "user,status",
    [
        ("create_user", status.HTTP_200_OK),
        (None, status.HTTP_401_UNAUTHORIZED),
    ],
)
def test_fully_update_sudoku(
    request, api_client, create_sudoku, sudoku_payload, user: str | None, status: int
) -> None:
    """Tests fully updating a sudoku is successful only when authenticated."""
    if user is not None:
        user = request.getfixturevalue(user)()
    client = api_client(user)
    sudoku = create_sudoku(user=user)

    url = sudoku_url(sudoku.id)
    response = client.put(url, sudoku_payload)

    assert response.status_code == status
    sudoku.refresh_from_db()
    if user is not None:
        for k, v in sudoku_payload.items():
            assert getattr(sudoku, k) == v
    else:
        assert sudoku.title == "sudoku title"
        assert sudoku.difficulty in SudokuDifficultyChoices.values
        assert sudoku.grid
        assert sudoku.status == SudokuStatusChoices.CREATED
    assert sudoku.user == user


def test_update_user_does_not_work(api_client, create_user, create_sudoku) -> None:
    """Tests that changing a sudoku's user does not work."""
    user = create_user()
    client = api_client(user)
    new_user = create_user()
    sudoku = create_sudoku(user=user)

    url = sudoku_url(sudoku.id)
    payload = {"user": new_user.id}
    response = client.patch(url, payload)
    assert response.status_code == status.HTTP_200_OK

    sudoku.refresh_from_db()
    assert sudoku.user == user


@pytest.mark.parametrize(
    "user,status,expectation",
    [
        ("create_user", status.HTTP_204_NO_CONTENT, pytest.raises(Sudoku.DoesNotExist)),
        (None, status.HTTP_401_UNAUTHORIZED, does_not_raise()),
    ],
)
def test_delete_sudoku(
    request, api_client, create_sudoku, user: str | None, status: int, expectation
) -> None:
    """Tests deleting a sudoku is successful only when authenticated."""
    if user is not None:
        user = request.getfixturevalue(user)()
    client = api_client(user)
    sudoku = create_sudoku(user=user)

    url = sudoku_url(sudoku.id)
    response = client.delete(url)
    assert response.status_code == status

    with expectation:
        Sudoku.objects.get(id=sudoku.id)


def test_delete_sudoku_does_not_work(api_client, create_user, create_sudoku) -> None:
    """Tests that deleting a sudoku that doesn't belong to the authenticated user does not work."""
    user = create_user()
    client = api_client(user)
    other_user = create_user()
    sudoku = create_sudoku(user=other_user)

    url = sudoku_url(sudoku.id)
    response = client.delete(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    assert sudoku.user == other_user
    assert Sudoku.objects.filter(id=sudoku.id).exists()


@pytest.mark.parametrize(
    "user",
    [
        "create_user",
        None,
    ],
)
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
    request, api_client, create_sudoku, user: str | None, difficulties: str, nb_sudokus: int
) -> None:
    """Tests filtering sudokus by difficulties."""
    if user is not None:
        user = request.getfixturevalue(user)()
    client = api_client(user)

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


@pytest.mark.parametrize(
    "user",
    [
        "create_user",
        None,
    ],
)
def test_retrieve_sudoku_solution_for_completed_sudoku(
    request, api_client, create_sudoku, user: str | None
) -> None:
    """Tests that retrieving a Sudoku solution for a completed sudoku is successful."""
    if user is not None:
        user = request.getfixturevalue(user)()
    client = api_client(user)

    sudoku = create_sudoku(user=user, status=SudokuStatusChoices.COMPLETED)
    sudoku_solution = SudokuSolution.objects.create(sudoku=sudoku)

    url = solution_url(sudoku.id)
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == str(sudoku_solution.id)
    assert response.data["sudoku_id"] == str(sudoku.id)
    assert response.data["grid"] == sudoku_solution.grid
    assert response.data["created_at"] == sudoku_solution.created_at.isoformat().replace(
        "+00:00", "Z"
    )
    assert response.data["updated_at"] == sudoku_solution.updated_at.isoformat().replace(
        "+00:00", "Z"
    )


@pytest.mark.parametrize(
    "user",
    [
        "create_user",
        None,
    ],
)
def test_retrieve_sudoku_solution_not_completed(
    request, api_client, create_sudoku, user: str | None
) -> None:
    """Tests that retrieving a Sudoku solution for a Sudoku that is not completed yet returns a
    404 status.
    """
    if user is not None:
        user = request.getfixturevalue(user)()
    client = api_client(user)
    sudoku = create_sudoku(user=user)

    url = solution_url(sudoku.id)
    response = client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data["detail"] == "Sudoku solution is not available yet"


@pytest.mark.parametrize(
    "user",
    [
        "create_user",
        None,
    ],
)
def test_retrieve_sudoku_nonexistent_solution(
    request, api_client, create_sudoku, user: str | None
) -> None:
    """Tests that retrieving a Sudoku solution that does not exist yet returns a 404 status."""
    if user is not None:
        user = request.getfixturevalue(user)()
    client = api_client(user)
    sudoku = create_sudoku(user=user, status=SudokuStatusChoices.COMPLETED)

    url = solution_url(sudoku.id)
    response = client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data["detail"] == "No solution found for this sudoku"


@pytest.mark.parametrize(
    "user",
    [
        "create_user",
        None,
    ],
)
def test_delete_sudoku_solution(
    monkeypatch, request, api_client, create_sudoku, create_sudoku_solution, user: str | None
) -> None:
    """Tests that deleting a solution is successful."""
    if user is not None:
        user = request.getfixturevalue(user)()
    client = api_client(user)

    sudoku = create_sudoku(user=user, status=SudokuStatusChoices.COMPLETED)
    sudoku_solution = create_sudoku_solution(sudoku=sudoku)

    def mock_update_sudoku_status(sudoku: Sudoku, status: SudokuStatusChoices) -> None:
        """Mock function to simulate `update_sudoku_status`."""
        sudoku.status = status
        sudoku.save(update_fields=["status"])

    monkeypatch.setattr("sudoku.views.update_sudoku_status", mock_update_sudoku_status)

    url = solution_url(sudoku.id)
    response = client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT

    with pytest.raises(SudokuSolution.DoesNotExist):
        SudokuSolution.objects.get(id=sudoku_solution.id)


@pytest.mark.parametrize(
    "user,status,expectation",
    [
        (
            "create_user",
            status.HTTP_204_NO_CONTENT,
            pytest.raises((Sudoku.DoesNotExist, SudokuSolution.DoesNotExist)),
        ),
        (None, status.HTTP_401_UNAUTHORIZED, does_not_raise()),
    ],
)
def test_delete_sudoku_also_deletes_solution(
    request,
    api_client,
    create_sudoku,
    create_sudoku_solution,
    user: str | None,
    status: int,
    expectation,
) -> None:
    """Tests that deleting a sudoku also deletes its solution."""
    if user is not None:
        user = request.getfixturevalue(user)()
    client = api_client(user)

    sudoku = create_sudoku(user=user, status=SudokuStatusChoices.COMPLETED)
    sudoku_solution = create_sudoku_solution(sudoku=sudoku)

    url = sudoku_url(sudoku.id)
    response = client.delete(url)

    assert response.status_code == status
    with expectation:
        Sudoku.objects.get(id=sudoku.id)
        SudokuSolution.objects.get(id=sudoku_solution.id)


def test_delete_solution_of_uncompleted_sudoku(
    api_client, create_user, create_sudoku, create_sudoku_solution
) -> None:
    """Tests that deleting the solution of an uncompleted sudoku returns a 409 status code."""
    user = create_user()
    client = api_client(user)

    sudoku = create_sudoku(user=user)
    create_sudoku_solution(sudoku=sudoku)

    url = solution_url(sudoku.id)
    response = client.delete(url)

    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.parametrize(
    "user",
    [
        "create_user",
        None,
    ],
)
def test_solve_sudoku_is_successful(
    request, monkeypatch, api_client, create_sudoku, user: str | None
) -> None:
    """Tests that solving a sudoku without being authenticated is successful."""
    if user is not None:
        user = request.getfixturevalue(user)()
    client = api_client(user)

    sudoku = create_sudoku(user=user)
    task_id = "12345"

    def mock_solve_view(self: SudokuViewSet, request: Request, pk: str | None = None) -> Response:
        """Mock function to simulate solve view."""
        sudoku = Sudoku.objects.get(id=pk)
        sudoku.task_id = task_id
        sudoku.status = SudokuStatusChoices.PENDING
        sudoku.save(update_fields=["status", "task_id"])
        return Response(
            {
                "status": "success",
                "message": "Sudoku solving started",
                "sudoku_id": pk,
                "task_id": task_id,
            }
        )

    monkeypatch.setattr("sudoku.views.SudokuViewSet.solve", mock_solve_view)

    url = solver_url(sudoku.id)
    response = client.post(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "success"
    assert response.data["message"] == "Sudoku solving started"
    assert response.data["sudoku_id"] == str(sudoku.id)
    assert response.data["task_id"] == task_id


@pytest.mark.parametrize(
    "user",
    [
        "create_user",
        None,
    ],
)
def test_abort_sudoku_solver_is_successful(
    request, monkeypatch, api_client, create_sudoku, user: str | None
) -> None:
    """Tests that aborting a sudoku solver task without being authenticated is successful."""
    if user is not None:
        user = request.getfixturevalue(user)()
    client = api_client(user)

    task_id = "12345"
    sudoku = create_sudoku(user=user, task_id=task_id, status=SudokuStatusChoices.RUNNING)

    def mock_abort_view(self: SudokuViewSet, request: Request, pk: str | None) -> Response:
        """Mock function to simulate abort view."""
        sudoku = Sudoku.objects.get(id=pk)
        sudoku.task_id = None
        sudoku.status = SudokuStatusChoices.ABORTED
        sudoku.save(update_fields=["task_id", "status"])
        return Response(
            {
                "status": "success",
                "message": "Sudoku solving aborted",
            }
        )

    monkeypatch.setattr("sudoku.views.SudokuViewSet.abort", mock_abort_view)

    url = solver_url(sudoku.id)
    response = client.delete(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "success"
    assert response.data["message"] == "Sudoku solving aborted"


@pytest.mark.parametrize(
    "user",
    [
        "create_user",
        None,
    ],
)
def test_get_sudoku_status(request, api_client, create_sudoku, user: str | None) -> None:
    """Tests that getting the status of a sudoku is successful."""
    if user is not None:
        user = request.getfixturevalue(user)()
    client = api_client(user)

    sudoku = create_sudoku(user=user, status=SudokuStatusChoices.RUNNING)

    url = status_url(sudoku.id)
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["sudoku_status"] == SudokuStatusChoices.RUNNING
