"""
Main FastAPI entry point for StadiumIQ.
Handles API routing, rate limiting, and CORS.
"""
import json
import re
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from backend.agents.copilot_agent import OperationsCopilot
from backend.agents.crowd_agent import CrowdAgent
from backend.agents.fan_agent import FanAssistAgent
from backend.agents.nav_agent import NavigationAgent
from backend.agents.scenario_agent import ScenarioAgent
from backend.agents.sustainability_agent import SustainabilityAgent
from backend.config import DEFAULT_RATE_LIMIT, MAX_QUERY_LENGTH, VERSION
from backend.context_manager import ContextManager
from backend.engines.crowd_risk_engine import CrowdRiskEngine
from backend.engines.graph_engine import NavigationGraph

load_dotenv()

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="StadiumIQ", version=VERSION)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://stadium-iq-rho.vercel.app", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

def sanitize_input(text: str, max_length: int = 500) -> str:
    text = text[:max_length]
    text = re.sub(r'[<>{}]', '', text)
    return text.strip()

graph = NavigationGraph("backend/data/stadium_map.json")
risk_engine = CrowdRiskEngine()
nav_agent = NavigationAgent(graph)
crowd_agent = CrowdAgent(risk_engine)
fan_agent = FanAssistAgent()
scenario_agent = ScenarioAgent(graph, risk_engine)
copilot = OperationsCopilot(risk_engine, graph)
sustainability_agent = SustainabilityAgent()


class ContextInput(BaseModel):
    current_time: str = Field(default="19:45", max_length=MAX_QUERY_LENGTH)
    match_phase: str = Field(default="halftime", max_length=MAX_QUERY_LENGTH)
    gate_status: dict = Field(
        default_factory=lambda: {"A": "open", "B": "open", "C": "closed", "D": "open"}
    )
    weather: str = Field(default="clear", max_length=MAX_QUERY_LENGTH)
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
    from_location: str = Field(max_length=MAX_QUERY_LENGTH)
    to_location: str = Field(max_length=MAX_QUERY_LENGTH)
    language: str = Field(default="English", max_length=MAX_QUERY_LENGTH)
    context: ContextInput = Field(default_factory=ContextInput)


class CrowdRequest(BaseModel):
    language: str = Field(default="English", max_length=MAX_QUERY_LENGTH)
    context: ContextInput = Field(default_factory=ContextInput)


class FanRequest(BaseModel):
    query: str = Field(max_length=MAX_QUERY_LENGTH)
    language: str = Field(default="English", max_length=MAX_QUERY_LENGTH)
    user_location: str = Field(default="", max_length=MAX_QUERY_LENGTH)
    accessibility_needs: str = Field(default="", max_length=MAX_QUERY_LENGTH)
    context: ContextInput = Field(default_factory=ContextInput)


class ScenarioRequest(BaseModel):
    scenario_type: str = Field(max_length=MAX_QUERY_LENGTH)
    scenario_params: dict = Field(default_factory=dict)
    language: str = Field(default="English", max_length=MAX_QUERY_LENGTH)
    context: ContextInput = Field(default_factory=ContextInput)


class CopilotRequest(BaseModel):
    language: str = Field(default="English", max_length=MAX_QUERY_LENGTH)
    context: ContextInput = Field(default_factory=ContextInput)

class SustainabilityRequest(BaseModel):
    language: str = Field(default="English", max_length=MAX_QUERY_LENGTH)
    context: ContextInput = Field(default_factory=ContextInput)


class TransportRequest(BaseModel):
    language: str = Field(default="English", max_length=MAX_QUERY_LENGTH)
    context: ContextInput = Field(default_factory=ContextInput)


def _context_from_input(context_input: ContextInput) -> ContextManager:
    return ContextManager.from_dict(context_input.model_dump())


@app.get("/health")
def health() -> dict:
    try:
        return {"status": "ok", "version": VERSION}
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
@limiter.limit(DEFAULT_RATE_LIMIT)
async def navigate(request: Request, body: NavigateRequest) -> dict:
    try:
        return await nav_agent.get_directions(
            body.from_location,
            body.to_location,
            body.language,
            _context_from_input(body.context),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/crowd")
@limiter.limit(DEFAULT_RATE_LIMIT)
async def crowd(request: Request, body: CrowdRequest) -> dict:
    try:
        return await crowd_agent.analyze(
            body.language,
            _context_from_input(body.context),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/fan")
@limiter.limit(DEFAULT_RATE_LIMIT)
async def fan(request: Request, body: FanRequest) -> str:
    try:
        sanitized_query = sanitize_input(body.query)
        return await fan_agent.answer(
            sanitized_query,
            body.language,
            _context_from_input(body.context),
            body.user_location,
            body.accessibility_needs,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/scenario")
@limiter.limit(DEFAULT_RATE_LIMIT)
async def scenario(request: Request, body: ScenarioRequest) -> dict:
    try:
        return await scenario_agent.simulate(
            body.scenario_type,
            body.scenario_params,
            body.language,
            _context_from_input(body.context),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/copilot")
@limiter.limit(DEFAULT_RATE_LIMIT)
async def copilot_priorities(request: Request, body: CopilotRequest) -> dict:
    try:
        return await copilot.get_priorities(
            body.language,
            _context_from_input(body.context),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/sustainability")
@limiter.limit(DEFAULT_RATE_LIMIT)
async def sustainability(request: Request, body: SustainabilityRequest) -> dict:
    try:
        return await sustainability_agent.get_eco_tip(
            body.language,
            _context_from_input(body.context),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/transport-status")
@limiter.limit("30/minute")
async def transport_status(request: Request, body: TransportRequest) -> dict:
    try:
        context = body.context
        return {
            "metro": context.nearby_transport.get("metro", "unknown"),
            "parking_north": context.nearby_transport.get("parking_north", "unknown"),
            "parking_south": context.nearby_transport.get("parking_south", "unknown"),
            "rideshare_wait": context.nearby_transport.get("rideshare", "unknown"),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
