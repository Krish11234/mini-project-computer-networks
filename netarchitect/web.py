"""NetArchitect FastAPI web dashboard backend."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from netarchitect.engines.config_generator import generate_full_config
from netarchitect.models import ScenarioInput
from netarchitect.orchestrator import run_design
from netarchitect.presets import list_presets, load_preset

app = FastAPI(
    title="NetArchitect Dashboard",
    description="Algorithmic Network Planning & Self-Explaining Architecture Engine",
    version="0.1.0",
)

_STATIC_DIR = Path(__file__).parent / "static"
_STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the main dashboard HTML."""
    html_path = _STATIC_DIR / "index.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@app.get("/api/presets")
async def api_list_presets():
    """Return list of available preset names."""
    return {"presets": list_presets()}


@app.get("/api/presets/{name}")
async def api_get_preset(name: str):
    """Return the raw JSON data for a preset."""
    try:
        scenario = load_preset(name)
        return scenario.model_dump(mode="json")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/design")
async def api_run_design(request: Request):
    """
    Accept a scenario JSON body, run the full pipeline, and return
    the complete NetworkDesign as JSON.
    """
    try:
        body = await request.json()
        scenario = ScenarioInput(**body)
        design = run_design(scenario)
        return design.model_dump(mode="json")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/config", response_class=PlainTextResponse)
async def api_generate_config(request: Request):
    """
    Accept a scenario JSON body, run the pipeline, and return the
    Cisco IOS configuration as plain text.
    """
    try:
        body = await request.json()
        scenario = ScenarioInput(**body)
        design = run_design(scenario)
        cfg = generate_full_config(design)
        return PlainTextResponse(cfg, media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def start_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Launch the Uvicorn dev server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server()
