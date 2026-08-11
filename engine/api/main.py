import json

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from engine.api.models import (
    ApproveRequest,
    ProvisionRequest,
    SessionState,
)
from engine.service import ProvisionService

app = FastAPI(
    title="InfraPilot Service",
    description="REST API for agentic infrastructure provisioning",
    version="1.0.0",
)

_service: ProvisionService | None = None


def get_service() -> ProvisionService:
    global _service
    if _service is None:
        _service = ProvisionService()
    return _service


def _state_from_session(session: dict | None):
    if session is None:
        return None
    return session.get("state")


def _build_response(session_id: str, session: dict) -> SessionState:
    status = session["status"]
    state = _state_from_session(session)
    error = session.get("error")

    return SessionState(
        session_id=session_id,
        status=status,
        project_name=state.project_name if state else None,
        provision_spec=state.provision_spec if state else None,
        generated_config=state.generated_config if state else None,
        validation_result=state.validation_result if state else None,
        approved=state.approved if state else None,
        execution_result=state.execution_result if state else None,
        error=error or (state.error if state else None),
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/provision", status_code=202)
async def start_provision(
    req: ProvisionRequest,
    svc: ProvisionService = Depends(get_service),
):
    session_id = await svc.start(
        user_request=req.user_request,
        project_name=req.project_name,
        example_id=req.example_id,
    )
    return {"session_id": session_id, "status": "pending"}


@app.get("/provision/{session_id}")
async def get_provision(
    session_id: str,
    svc: ProvisionService = Depends(get_service),
):
    session = svc.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return _build_response(session_id, session)


@app.post("/provision/{session_id}/approve")
async def approve_provision(
    session_id: str,
    req: ApproveRequest,
    svc: ProvisionService = Depends(get_service),
):
    try:
        session = await svc.approve(
            session_id=session_id,
            approved=req.approved,
            feedback=req.feedback,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return _build_response(session_id, session)


@app.get("/provision/{session_id}/events")
async def provision_events(
    session_id: str,
    svc: ProvisionService = Depends(get_service),
):
    """Server-Sent Events endpoint for real-time pipeline progress."""
    queue = svc.get_event_queue(session_id)
    if queue is None:
        raise HTTPException(status_code=404, detail="Session not found")

    async def event_stream():
        sent = 0
        while True:
            events = list(queue)
            new_events = events[sent:]
            for evt in new_events:
                yield f"data: {json.dumps(evt)}\n\n"
            sent = len(events)

            session = svc.get_session(session_id)
            if session and session["status"] in ("completed", "failed"):
                break

            import asyncio
            await asyncio.sleep(0.5)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# Serve the frontend
app.mount(
    "/",
    StaticFiles(directory="engine/api/static", html=True),
    name="static",
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "engine.api.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
