from fastapi import status
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from sqlalchemy.orm import Session

from src.app.api.dependencies import get_current_user
from src.app.api.v1.users import oauth2_scheme
from tests.conftest import fake, override_dependency

from .helpers import generators, mocks


def test_post_document(client: TestClient) -> None:
    response = client.post(
        "/api/v1/document",
        json={
    "filename": "my_notes.pdf",
    "content_type": "application/pdf",
    "size": 100
        },
    )
    assert response.status_code == status.HTTP_201_CREATED