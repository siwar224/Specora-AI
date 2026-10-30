"""FastAPI application for Specora AI.

Specora's first test flow is intentionally small:

    product idea -> LLM -> structured specification -> browser review

Audio transcription remains available as an optional input endpoint, but it is
not mixed with the specification-generation contract.
"""

import os
import tempfile

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import actions
import stt
import understand


load_dotenv()

app = FastAPI(title="Specora AI", version="0.1.0")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


# ---------------------------------------------------------------------------
# API models
# ---------------------------------------------------------------------------
class SpecificationRequest(BaseModel):
    """The raw product idea submitted by the user."""

    raw_idea: str = Field(..., min_length=1, description="The user's product idea")


# ---------------------------------------------------------------------------
# Health and product metadata
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health() -> dict:
    """Return enough configuration information for the test interface."""
    backend = understand.active_backend()
    return {
        "ok": True,
        "llm_backend": backend,
        "llm_configured": bool(os.getenv("OPENAI_API_KEY")) if backend == "openai" else True,
        "transcription_backend": stt.active_backend(),
        "transcription_configured": bool(os.getenv("OPENAI_API_KEY"))
        if stt.active_backend() == "openai"
        else True,
    }


@app.get("/api/specification-sections")
def specification_sections() -> dict:
    """Expose the section labels used by the browser review interface."""
    return {"sections": actions.SPECIFICATION_SECTION_LABELS}


# ---------------------------------------------------------------------------
# Specora generation endpoint
# ---------------------------------------------------------------------------
@app.post("/api/specifications/generate")
def generate_specification(req: SpecificationRequest) -> JSONResponse:
    """Generate one structured specification from a product idea."""
    result = understand.understand(req.raw_idea)

    if result.get("type") == "error":
        return JSONResponse(
            {"stage": "generation", **result},
            status_code=502,
        )

    return JSONResponse(actions.build_specification_response(req.raw_idea, result))


# ---------------------------------------------------------------------------
# Optional audio input
# ---------------------------------------------------------------------------
@app.post("/api/transcribe")
async def transcribe(audio: UploadFile) -> JSONResponse:
    """Transcribe an uploaded audio file so the UI can use it as an idea."""
    suffix = os.path.splitext(audio.filename or "")[1] or ".wav"
    tmp_path = None
    try:
        data = await audio.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(data)
            tmp_path = tmp.name

        return JSONResponse(stt.transcribe(tmp_path))
    except stt.STTError as exc:
        return JSONResponse({"type": "error", "stage": "transcription", "error": str(exc)}, status_code=502)
    except Exception as exc:
        return JSONResponse(
            {"type": "error", "stage": "transcription", "error": f"Unexpected: {exc}"},
            status_code=500,
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


# ---------------------------------------------------------------------------
# Static test interface
# ---------------------------------------------------------------------------
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))
