"""Regression tests for the transcription error-handling fix.

A pipeline failure inside run_transcription must mark the task FAILED
(not leave it stuck IN_PROGRESS). A corrupt upload must produce a clean
HTTP error without hanging the service.
"""
from io import BytesIO

from fastapi.testclient import TestClient

from backend.main import app
from backend.db.task.models import TaskStatus
from backend.routers.transcription import router as transcription_router
from backend.tests.test_backend_config import TEST_FILE_PATH


class FailingPipeline:
    def run(self, *args, **kwargs):
        raise RuntimeError("injected pipeline failure")


def test_pipeline_failure_marks_task_failed(monkeypatch):
    monkeypatch.setattr(transcription_router, "get_pipeline", lambda: FailingPipeline())
    client = TestClient(app, raise_server_exceptions=False)
    with client:
        with open(TEST_FILE_PATH, "rb") as f:
            response = client.post(
                "/transcription/",
                files={"file": ("jfk.wav", f, "audio/wav")},
            )
        assert response.status_code == 201
        identifier = response.json()["identifier"]
        task = client.get(f"/task/{identifier}")
        assert task.status_code == 200
        assert task.json()["status"] == TaskStatus.FAILED
        assert "injected pipeline failure" in task.json()["error"]


def test_corrupt_file_returns_clean_error():
    client = TestClient(app, raise_server_exceptions=False)
    with client:
        response = client.post(
            "/transcription/",
            files={"file": ("bad.mp3", BytesIO(b"this is not audio"), "audio/mpeg")},
        )
        assert response.status_code in (400, 422, 500)
        assert client.get("/docs").status_code == 200
