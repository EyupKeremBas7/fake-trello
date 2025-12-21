"""
Uploads endpoint tests.
Covers: /uploads/*
"""
from locust import task, tag, between

from .base import AuthenticatedBaseUser, BaseUser


class UploadsAPIUser(BaseUser):
    """Tests for public file access endpoint."""
    wait_time = between(1, 2)
    weight = 1

    @task
    @tag('uploads')
    def get_nonexistent_file(self):
        """Test GET /uploads/files/{filename} - non-existent file (expected 404)."""
        with self.client.get(
            "/api/v1/uploads/files/nonexistent.png",
            name="[Uploads] Get File 404",
            catch_response=True
        ) as response:
            if response.status_code == 404:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")


class UploadImageUser(AuthenticatedBaseUser):
    """Tests for image upload endpoint."""
    wait_time = between(2, 4)
    weight = 1

    @task
    @tag('uploads', 'create')
    def upload_invalid_image(self):
        """Test POST /uploads/image with invalid file type (expected 400)."""
        with self.client.post(
            "/api/v1/uploads/image",
            headers=self.headers,
            files={"file": ("test.txt", b"invalid content", "text/plain")},
            name="[Uploads] Upload Invalid",
            catch_response=True
        ) as response:
            if response.status_code == 400:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")
