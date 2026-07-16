import json
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from backend.agents.copilot_agent import OperationsCopilot
from backend.agents.crowd_agent import CrowdAgent
from backend.agents.fan_agent import FanAssistAgent
from backend.agents.nav_agent import NavigationAgent
from backend.agents.scenario_agent import ScenarioAgent
from backend.context_manager import ContextManager
from backend.engines.crowd_risk_engine import CrowdRiskEngine
from backend.engines.graph_engine import NavigationGraph


load_dotenv()

app = FastAPI(title="StadiumIQ", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = NavigationGraph("backend/data/stadium_map.json")
risk_engine = CrowdRiskEngine()
nav_agent = NavigationAgent(graph)
crowd_agent = CrowdAgent(risk_engine)
fan_agent = FanAssistAgent()
scenario_agent = ScenarioAgent(graph, risk_engine)
copilot = OperationsCopilot(risk_engine, graph)


class ContextInput(BaseModel):
    current_time: str = "19:45"
    match_phase: str = "halftime"
    gate_status: dict = Field(
        default_factory=lambda: {"A": "open", "B": "open", "C": "closed", "D": "open"}
    )
    weather: str = "clear"
    queue_times: dict = Field(
        default_factory=lambda: {
            "food_court_a": 25,
            "food_court_b": 5,
            "restroom_north": 3,
        }
    )
    section_occupancy: dict = Field(
        default_factory=lambda: {
            "A1": 85,
            "A2": 40,
            "B1": 92,
            "B2": 55,
            "C1": 70,
            "C2": 30,
        }
    )
    nearby_transport: dict = Field(
        default_factory=lambda: {
            "metro": "available",
            "rideshare": "15min_wait",
            "parking_north": "full",
            "parking_south": "available",
        }
    )


class NavigateRequest(BaseModel):
    from_location: str
    to_location: str
    language: str = "English"
    context: ContextInput = Field(default_factory=ContextInput)


class CrowdRequest(BaseModel):
    language: str = "English"
    context: ContextInput = Field(default_factory=ContextInput)


class FanRequest(BaseModel):
    query: str
    language: str = "English"
    user_location: str = ""
    accessibility_needs: str = ""
    context: ContextInput = Field(default_factory=ContextInput)


class ScenarioRequest(BaseModel):
    scenario_type: str
    scenario_params: dict = Field(default_factory=dict)
    language: str = "English"
    context: ContextInput = Field(default_factory=ContextInput)


class CopilotRequest(BaseModel):
    language: str = "English"
    context: ContextInput = Field(default_factory=ContextInput)


def _context_from_input(context_input: ContextInput) -> ContextManager:
    return ContextManager.from_dict(context_input.model_dump())


@app.get("/health")
def health() -> dict:
    try:
        return {"status": "ok", "version": "1.0.0"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/")
def get_index():
    try:
        index_path = Path(__file__).resolve().parent.parent / "docs" / "index.html"
        with index_path.open("r", encoding="utf-8") as file:
            return HTMLResponse(content=file.read(), status_code=200)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/stadium-map")
def stadium_map() -> dict:
    try:
        map_path = Path(__file__).resolve().parent / "data" / "stadium_map.json"
        with map_path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/navigate")
def navigate(request: NavigateRequest) -> dict:
    try:
        return nav_agent.get_directions(
            request.from_location,
            request.to_location,
            request.language,
            _context_from_input(request.context),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/crowd")
def crowd(request: CrowdRequest) -> dict:
    try:
        return crowd_agent.analyze(
            request.language,
            _context_from_input(request.context),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/fan")
def fan(request: FanRequest) -> str:
    try:
        return fan_agent.answer(
            request.query,
            request.language,
            _context_from_input(request.context),
            request.user_location,
            request.accessibility_needs,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/scenario")
def scenario(request: ScenarioRequest) -> dict:
    try:
        return scenario_agent.simulate(
            request.scenario_type,
            request.scenario_params,
            request.language,
            _context_from_input(request.context),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/copilot")
def copilot_priorities(request: CopilotRequest) -> dict:
    try:
        return copilot.get_priorities(
            request.language,
            _context_from_input(request.context),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
