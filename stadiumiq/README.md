# StadiumIQ — Operational Intelligence Platform for FIFA World Cup 2026

## Overview
StadiumIQ is a hybrid AI platform combining deterministic decision engines with Generative AI to optimize stadium operations at FIFA World Cup 2026. It serves fans, venue staff, organizers, and volunteers through intelligent navigation, crowd safety management, multilingual assistance, scenario simulation, and autonomous operational reasoning.

## Chosen Vertical
Smart Stadiums & Tournament Operations

## Design Principles
- **Deterministic before Generative**: Algorithms compute paths, scores, and impacts. Gemini reasons and communicates — never the reverse.
- **Context-first**: Every AI call includes live stadium state (time, phase, gates, occupancy, queues, weather). No generic responses.
- **Layered architecture**: Engines → Agents → API → UI. Each layer has a single responsibility.
- **Operational, not conversational**: The system behaves like infrastructure, not a chatbot.

## Architecture
```text
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend UI                              │
│  Context Panel | SmartNav | CrowdPulse | FanAssist | ScenarioSim │
│                         Operations Copilot                       │
└───────────────────────────────┬─────────────────────────────────┘
                                │ fetch() JSON over HTTP
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                          │
│ /navigate | /crowd | /fan | /scenario | /copilot | /stadium-map  │
└───────────────────────────────┬─────────────────────────────────┘
                                │ ContextManager per request
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                            Agents                                │
│ NavigationAgent | CrowdAgent | FanAssistAgent | ScenarioAgent    │
│ OperationsCopilot                                                │
└───────────────┬───────────────────────────────┬─────────────────┘
                │ deterministic outputs          │ AI explanation
                ▼                               ▼
┌──────────────────────────────┐    ┌─────────────────────────────┐
│            Engines            │    │        Google Gemini         │
│ NavigationGraph + Dijkstra    │    │ gemini-1.5-flash             │
│ CrowdRiskEngine rules         │    │ multilingual reasoning       │
└───────────────┬──────────────┘    └─────────────────────────────┘
                │
                ▼
┌──────────────────────────────┐
│ backend/data/stadium_map.json │
│ 24-node weighted venue graph  │
└──────────────────────────────┘
```

## Modules

### SmartNav (Navigation Agent + Graph Engine)
- Dijkstra's algorithm on a 24-node weighted stadium graph
- Dynamically avoids high-occupancy nodes
- Redirects when destination gate is closed
- Gemini converts computed path to step-by-step directions in EN/HI/ES

### CrowdPulse (Crowd Agent + Risk Engine)
- Rule-based risk scoring: occupancy + match phase + weather + choke point proximity + queue overflow
- Computes per-section risk (low/medium/high/critical) and concourse pressure
- Gemini explains reasoning and recommends prioritized staff actions

### FanAssist (Fan Agent)
- Context-injected Q&A: live queue times, gate status, match phase, transport, accessibility needs
- Recommends shortest food queue, warns on congestion, adapts to accessibility requirements
- Responds in English, Hindi (Devanagari), or Spanish

### ScenarioSim (Scenario Agent)
- Simulates gate closure, section overflow, emergency evacuation
- Computes: affected fans, severity, recovery time, required volunteers, alternate routes
- Gemini produces structured operational response plan

### Operations Copilot
- Analyzes entire stadium state autonomously
- Ranks top 3 operational priorities with staff assignments and resolution timelines
- Designed for organizers asking: "What should we do right now?"

## How the Solution Works
1. Operator sets live context (time, match phase, gate status, occupancy, queues) in the UI
2. Context is sent in the body of every API call
3. Deterministic engines process data first — paths, scores, impact estimates
4. Gemini receives structured output and provides human-readable reasoning in the chosen language
5. Frontend renders results as visual cards, breadcrumbs, chat, and priority panels

## Tech Stack
| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, Uvicorn |
| AI | Google Gemini 1.5 Flash |
| Navigation | Custom Dijkstra on adjacency list |
| Risk Engine | Rule-based scoring (pure Python) |
| Frontend | Vanilla HTML/CSS/JS |
| Testing | pytest, unittest.mock |

## Setup & Run
```bash
git clone <your-repo-url>
cd stadiumiq
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your Gemini API key
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
# In browser: open frontend/index.html
```

## Testing
```bash
cd backend
pytest tests/ -v
# Expected: 26 tests, all passing
```

## Scalability Considerations
- Graph engine is stateless and thread-safe; scales horizontally
- Context Manager is per-request (no shared mutable state)
- Gemini calls are the only external dependency; can be swapped for local LLM
- Stadium map is JSON-driven; any venue can be onboarded by replacing the file

## Limitations
- Section occupancy is operator-input (simulates sensor feeds; no real IoT integration)
- Fan count estimates are approximations (500 fans per section unit)
- Hindi output quality depends on Gemini's Devanagari generation capability
- Navigation graph covers MetLife Stadium only

## Future Improvements
- Real-time IoT sensor integration for automatic occupancy updates
- Computer vision crowd density estimation from CCTV feeds
- Push notifications to fan mobile app for dynamic rerouting
- Historical data layer for predictive crowd modeling
- Integration with public transport APIs for live shuttle/metro updates

## Assumptions Made
- Stadium map is static; gate/section state is operator-controlled
- 500 fans per section is a conservative mock estimate
- All three languages use left-to-right rendering (Hindi Devanagari is LTR-compatible in browsers)
- Backend runs locally on port 8000 during evaluation

## Screenshots
### Live Context + Navigation
![Live Context and Navigation](docs/screenshots/01-dashboard-navigate.png)

### Crowd Monitor
![Crowd Monitor](docs/screenshots/02-crowd-monitor.png)

### Scenario Simulator
![Scenario Simulator](docs/screenshots/03-scenario-simulator.png)
