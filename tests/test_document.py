from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from src.app.api.dependencies import get_current_user
from src.app.api.v1.users import oauth2_scheme
from tests.conftest import fake, override_dependency
from .helpers import generators, mocks

def test_post_document(db: Session, client: TestClient) -> None:
    user = generators.create_user(db)

    override_dependency(get_current_user, mocks.get_current_user(user))

    # Compose the JSON payload with all required fields, including s3_url
    payload = {
        "filename": "my_notes.pdf",
        "content_type": "application/pdf",
        "size": 100,
        "s3_url": "https://mybucket.s3.amazonaws.com/my_notes.pdf"
    }

    response = client.post(
        "/api/v1/document",
        json=payload,
    )

    assert response.status_code == status.HTTP_201_CREATED, "Error message JSON: " + response.text
    data = response.json()
    assert data["filename"] == payload["filename"]
    assert data["s3_url"] == payload["s3_url"]
    assert data["created_by_user_id"] == user.id