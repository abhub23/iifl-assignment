import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.db import EntryStore
from app.llm import AIParseError, _extract_text, _parse_ai_output
from app.main import app as fastapi_app
from app.main import settings as main_settings
from app.schemas import AIResult


@pytest.fixture()
def store(tmp_path, monkeypatch) -> EntryStore:
    """Point the app at a throwaway SQLite file for every test."""
    from app import main

    test_store = EntryStore(tmp_path / "test.db")
    test_store.init()
    monkeypatch.setattr(main, "store", test_store)
    return test_store


@pytest.fixture()
def client(store) -> TestClient:
    # No context manager on purpose: lifespan must not touch the real DB path.
    return TestClient(fastapi_app)


@pytest.fixture()
def canned_ai(monkeypatch):
    """Replace the real Gemini call with a deterministic result."""

    async def fake(text: str, settings=None) -> AIResult:
        return AIResult(summary="A concise summary.", tags=["alpha", "beta", "gamma"])

    monkeypatch.setattr("app.main.generate_summary_and_tags", fake)
    return fake


class TestHealth:
    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestCreateEntry:
    def test_create_persists_entry(self, client, store, canned_ai):
        text = "Some meeting notes about Q3 plans."
        response = client.post("/entries", json={"text": text})
        assert response.status_code == 201

        body = response.json()
        assert body["id"] > 0
        assert body["original_text"] == text
        assert body["summary"] == "A concise summary."
        assert body["tags"] == ["alpha", "beta", "gamma"]
        assert body["created_at"]

        assert len(store.list()) == 1

    def test_empty_text_rejected(self, client, canned_ai):
        for payload in [{"text": ""}, {"text": "   \n\t"}]:
            response = client.post("/entries", json=payload)
            assert response.status_code == 400
            assert "empty" in response.json()["detail"].lower()

    def test_missing_text_field_rejected(self, client):
        response = client.post("/entries", json={})
        assert response.status_code == 422

    def test_too_long_text_rejected(self, client, monkeypatch, canned_ai):
        monkeypatch.setattr(main_settings, "max_text_length", 50)
        response = client.post("/entries", json={"text": "a" * 51})
        assert response.status_code == 400
        assert "maximum length" in response.json()["detail"]

    def test_malformed_ai_output_surfaces_502(self, client, monkeypatch):
        async def bad_parse(text: str, settings=None) -> AIResult:
            raise AIParseError("AI returned invalid JSON")

        monkeypatch.setattr("app.main.generate_summary_and_tags", bad_parse)

        response = client.post("/entries", json={"text": "valid text"})
        assert response.status_code == 502
        assert "invalid JSON" in response.json()["detail"]
        # nothing was persisted on failure
        assert len(client.get("/entries").json()) == 0

    def test_timeout_surfaces_502(self, client, monkeypatch):
        from app.llm import AIServiceError

        async def timeout(text: str, settings=None) -> AIResult:
            raise AIServiceError("the AI request timed out")

        monkeypatch.setattr("app.main.generate_summary_and_tags", timeout)

        response = client.post("/entries", json={"text": "valid text"})
        assert response.status_code == 502
        assert "timed out" in response.json()["detail"]


class TestListAndGetEntries:
    def test_list_returns_newest_first(self, client, store, canned_ai):
        for i in range(3):
            client.post("/entries", json={"text": f"note {i}"})

        entries = client.get("/entries").json()
        assert [entry["original_text"] for entry in entries] == ["note 2", "note 1", "note 0"]

    def test_get_entry_detail(self, client, store, canned_ai):
        created = client.post("/entries", json={"text": "hello"}).json()
        fetched = client.get(f"/entries/{created['id']}").json()
        assert fetched["id"] == created["id"]
        assert fetched["original_text"] == "hello"

    def test_get_missing_entry_404(self, client, store):
        response = client.get("/entries/9999")
        assert response.status_code == 404


class TestAIParsing:
    """Direct tests of the defensive parser (no HTTP involved)."""

    GEMINI_BODY = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": '{"summary": "Short summary.", "tags": ["one", "two", "three"]}'}
                    ]
                }
            }
        ]
    }

    def test_extracts_and_parses_clean_response(self):
        raw = _extract_text(self.GEMINI_BODY)
        result = _parse_ai_output(raw)
        assert result.summary == "Short summary."
        assert result.tags == ["one", "two", "three"]

    def test_handles_markdown_fences(self):
        raw = '```json\n{"summary": "s", "tags": ["a", "b", "c"]}\n```'
        result = _parse_ai_output(raw)
        assert result.tags == ["a", "b", "c"]

    def test_rejects_invalid_json(self):
        with pytest.raises(AIParseError):
            _parse_ai_output("this is not JSON at all")

    def test_rejects_wrong_tag_count(self):
        with pytest.raises(AIParseError):
            _parse_ai_output('{"summary": "s", "tags": ["a", "b"]}')

    def test_schema_requires_three_tags(self):
        with pytest.raises(ValidationError):
            AIResult(summary="s", tags=["only-one"])

    def test_unexpected_gemini_shape_raises_parse_error(self):
        with pytest.raises(AIParseError):
            _extract_text({"candidates": []})
