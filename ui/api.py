import json
import time
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

from state import initial_state
from graph import app as langgraph_app
from scenarios.inputs import (
    PRODUCT_LAUNCH_SPEC,
    COMPLIANCE_CHECK_SAMPLE,
    ENGAGEMENT_DATA_SAMPLE,
)

api = FastAPI(title="ET Content Ops Agent API")

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    scenario: str   # "product_launch" | "compliance_check" | "performance_pivot" | "custom"
    custom_input: str = ""


SCENARIO_MAP = {
    "product_launch":    ("PRODUCT_SPEC",     PRODUCT_LAUNCH_SPEC),
    "compliance_check":  ("COMPLIANCE_CHECK", COMPLIANCE_CHECK_SAMPLE),
    "performance_pivot": ("ENGAGEMENT_DATA",  ENGAGEMENT_DATA_SAMPLE),
}


@api.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@api.post("/run")
def run_pipeline(req: RunRequest):
    """Run a scenario and return the full final state."""
    os.environ["DEMO_AUTO_APPROVE"] = "true"

    if req.scenario == "custom":
        if not req.custom_input.strip():
            raise HTTPException(400, "custom_input required when scenario=custom")
        input_type = "PRODUCT_SPEC"
        raw_input = req.custom_input
    else:
        if req.scenario not in SCENARIO_MAP:
            raise HTTPException(400, f"Unknown scenario. Choose from: {list(SCENARIO_MAP)}")
        input_type, raw_input = SCENARIO_MAP[req.scenario]

    start = time.perf_counter()
    state = initial_state(input_type, raw_input)
    final_state = langgraph_app.invoke(state)
    elapsed = round(time.perf_counter() - start, 2)

    # Serialise state
    out = {k: (v if isinstance(v, (str, int, float, bool, list, dict, type(None))) else str(v))
           for k, v in final_state.items()}
    out["elapsed_seconds"] = elapsed
    return out


@api.get("/scenarios")
def list_scenarios():
    return {
        "scenarios": [
            {"id": "product_launch",    "name": "Product Launch Sprint",  "input_type": "PRODUCT_SPEC"},
            {"id": "compliance_check",  "name": "Compliance Rejection",   "input_type": "COMPLIANCE_CHECK"},
            {"id": "performance_pivot", "name": "Performance Pivot",      "input_type": "ENGAGEMENT_DATA"},
            {"id": "custom",            "name": "Custom Input",           "input_type": "auto-detect"},
        ]
    }
