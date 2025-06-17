import io
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from src.app.api.dependencies import get_current_user
from src.app.api.v1.users import oauth2_scheme
from tests.conftest import override_dependency
from .helpers import generators, mocks

def test_upload_file_success(db: Session, client: TestClient, mocker) -> None:
    user = generators.create_user(db)

    override_dependency(get_current_user, mocks.get_current_user(user))
    override_dependency(oauth2_scheme, mocks.oauth2_scheme())

    mocker.patch("src.app.api.v1.upload.upload_file_to_s3", return_value="some/key/test.pdf")
    mocker.patch("src.app.api.v1.upload.generate_s3_url", return_value="https://mocked-s3-url.com/test.pdf")

    file_data = io.BytesIO(b"Dummy PDF content")
    file_data.name = "test_upload.pdf"

    response = client.post(
        "/api/v1/upload",
        files={"file": ("test_upload.pdf", file_data, "application/pdf")},
    )

    assert response.status_code == 200, "Error message JSON: " + response.text  
    data = response.json()
    assert "key" in data
    assert "url" in data
    assert data["url"] == "https://mocked-s3-url.com/test.pdf"
