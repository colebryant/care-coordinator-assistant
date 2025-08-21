import json
import uuid

import httpx
from agent import run_message_stream, set_patient_context
from config import settings
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from models import ChatRequest, SessionStartRequest, SessionStartResponse

app = FastAPI(title="Care Coordinator Assistant API")


@app.get("/healthcheck")
def healthcheck():
    return {"status": "ok"}


@app.post("/api/session/start", response_model=SessionStartResponse)
def start_session(req: SessionStartRequest):
    """Validate patient_id, seed thread state with patient context, and return a new thread_id."""
    url = f"{settings.CONTEXTUAL_API_URL}/{req.patient_id}"
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(url)
            if r.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid patient_id or patient not found",
                )
            data = r.json()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Upstream error fetching patient data: {e}",
        )

    thread_id = str(uuid.uuid4())
    ok = set_patient_context(thread_id, data, reset=True)
    if not ok:
        raise HTTPException(
            status_code=500, detail="Failed to initialize session context"
        )
    return SessionStartResponse(
        thread_id=thread_id,
        patient_id=req.patient_id,
        patient_name=data["name"],
    )


@app.post("/api/chat/stream")
def chat_stream(req: ChatRequest):
    """Streaming chat endpoint using Server-Sent Events"""

    def generate():
        try:
            for chunk in run_message_stream(
                req.message, thread_id=req.thread_id, reset=req.reset
            ):
                # Format as Server-Sent Events
                yield f"data: {json.dumps({'content': chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
