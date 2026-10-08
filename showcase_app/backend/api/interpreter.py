"""
showcase_app/backend/api/interpreter.py — Live Interpreter Execution & SSE Streaming.
"""

import json
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from showcase_app.backend.schemas import InterpreterRunRequest, InterpreterRunResponse
from showcase_app.backend.services.interpreter_service import interpreter_service

router = APIRouter()

# Memory store for recent executions
RUN_STORE: Dict[str, Dict[str, Any]] = {}


@router.post("/interpreter/runs")
async def start_interpreter_run(req: InterpreterRunRequest):
    """
    Executes a real workflow through PolyCellRuntime (normal or controlled failure injection).
    """
    mode = req.mode if req.mode in ["normal", "failure"] else "normal"
    res = await interpreter_service.execute_run(mode=mode, feature_id=req.feature_id)
    run_id = res.get("run_id", f"run_{id(res)}")
    RUN_STORE[run_id] = res
    return res


@router.get("/interpreter/runs/{run_id}")
def get_interpreter_run(run_id: str):
    if run_id not in RUN_STORE:
        raise HTTPException(status_code=404, detail="Interpreter run not found")
    return RUN_STORE[run_id]


@router.get("/interpreter/runs/{run_id}/events")
async def stream_interpreter_events(run_id: str, mode: str = Query("normal")):
    """
    Server-Sent Events (SSE) streaming live cell executions and receipts.
    """
    async def event_generator():
        async for event in interpreter_service.stream_execution(mode=mode, run_id=run_id):
            data_json = json.dumps(event)
            yield f"data: {data_json}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
