import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import EntryStore
from app.llm import AIParseError, AIServiceError, generate_summary_and_tags
from app.schemas import AIResult, EntryCreate, EntryOut

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()
store = EntryStore(settings.database_path)


@asynccontextmanager
async def lifespan(_: FastAPI):
    store.init()
    logger.info("database ready at %s", settings.database_path)
    yield


app = FastAPI(title="AI Content Assistant", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _validate_text(text: str) -> str:
    cleaned = text.strip() if isinstance(text, str) else ""
    if not cleaned:
        raise HTTPException(status_code=400, detail="Text must not be empty")
    if len(cleaned) > settings.max_text_length:
        raise HTTPException(
            status_code=400,
            detail=f"Text exceeds the maximum length of {settings.max_text_length} characters",
        )
    return cleaned


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/entries", response_model=EntryOut, status_code=201)
async def create_entry(payload: EntryCreate) -> dict:
    text = _validate_text(payload.text)

    try:
        result: AIResult = await generate_summary_and_tags(text)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=f"AI service error: {exc}") from exc
    except AIParseError as exc:
        raise HTTPException(status_code=502, detail=f"AI returned malformed output: {exc}") from exc

    entry = store.create(original_text=text, summary=result.summary, tags=result.tags)
    logger.info("created entry id=%s tags=%s", entry["id"], entry["tags"])
    return entry


@app.get("/entries", response_model=list[EntryOut])
async def list_entries() -> list[dict]:
    return store.list()


@app.get("/entries/{entry_id}", response_model=EntryOut)
async def get_entry(entry_id: int) -> dict:
    entry = store.get(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry
