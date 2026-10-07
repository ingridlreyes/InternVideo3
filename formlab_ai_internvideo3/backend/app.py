from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .internvideo3_service import ENABLE, MODEL_ID, service

app = FastAPI(title="FormLab AI backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup() -> None:
    # Deliberately lazy. Loading an 8B video model is expensive, so the
    # service loads it only when enabled with FORMLAB_ENABLE_INTERNVIDEO3=1.
    if ENABLE and os.getenv("FORMLAB_EAGER_LOAD", "0").lower() in {"1","true","yes"}:
        service.load()

@app.get("/api/health")
def health() -> dict:
    if ENABLE and not service.ready and service.error is None:
        # Do not force a heavyweight load just to answer health.
        status = "enabled_not_loaded"
    elif service.ready:
        status = "ready"
    elif service.error:
        status = "error"
    else:
        status = "disabled"
    return {
        "ok": True,
        "internvideo3_enabled": ENABLE,
        "internvideo3_ready": service.ready,
        "internvideo3_status": status,
        "model_id": MODEL_ID,
        "error": service.error,
    }

@app.post("/api/deep-analyze")
async def deep_analyze(
    video: UploadFile = File(...),
    exercise: str = Form(...),
    biomechanics_json: str = Form("{}"),
    user_question: str = Form(""),
) -> dict:
    if exercise not in {"squat","lunge","single_leg_rdl","conventional_deadlift"}:
        raise HTTPException(400, "exercise must be squat, lunge, single_leg_rdl, or conventional_deadlift")
    if not ENABLE:
        raise HTTPException(
            503,
            "InternVideo3 is disabled. Set FORMLAB_ENABLE_INTERNVIDEO3=1 and restart the backend."
        )
    try:
        biomechanics = json.loads(biomechanics_json)
    except json.JSONDecodeError:
        raise HTTPException(400, "biomechanics_json must be valid JSON")

    suffix = Path(video.filename or "video.mp4").suffix.lower()
    if suffix not in {".mp4",".mov",".m4v",".webm",".avi",".mkv"}:
        suffix = ".mp4"

    with tempfile.NamedTemporaryFile(prefix="formlab_", suffix=suffix, delete=False) as tmp:
        tmp_path = tmp.name
        total = 0
        while chunk := await video.read(1024 * 1024):
            total += len(chunk)
            if total > 500 * 1024 * 1024:
                Path(tmp_path).unlink(missing_ok=True)
                raise HTTPException(413, "Video exceeds 500 MB.")
            tmp.write(chunk)

    try:
        analysis = service.analyze(
            video_path=tmp_path,
            exercise=exercise,
            biomechanics=biomechanics,
            user_question=user_question,
        )
        return {
            "model": MODEL_ID,
            "exercise": exercise,
            "analysis_text": analysis,
            "biomechanics_source": "browser-derived MediaPipe measurements supplied with request",
        }
    except Exception as exc:
        raise HTTPException(503, f"InternVideo3 analysis failed: {exc}")
    finally:
        Path(tmp_path).unlink(missing_ok=True)
