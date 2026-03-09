# Backend Agent Prompt
*Copy and paste the text below directly into the chat with the Backend Agent to begin the integration phase.*

***

Hello Backend Agent! We are preparing the SmartFlow AI project for a hackathon MVP. The frontend is currently faking most of its data because the backend generates a generic mathematical 5x5 grid (`I-101`, `I-102`...) instead of the geographic nodes we map on the frontend. We need to rewire the backend (FastAPI) to simulate actual geographic nodes, handle live emergency preemption, and add Machine Learning congestion prediction.

Here are your core epics:

### 1. Topographical Synchronization
- Our frontend uses `civilLinesSignals` (defining Python dictionaries/models for nodes like `S1`, `S2` with `[lat, lng]`) and `civilLinesEdges` (defining spatial road connections). Please ask the user for these structures so you can ingest this graph into the backend.
- Refactor the `TrafficSimulation` engine. Vehicles must traverse these specific edges and nodes, not a generic 5x5 array.
- Update `GET /api/grid/state` to return these `S1` IDs natively, along with their true simulated vehicle density and `GREEN`/`RED` signal phases.

### 2. Emergency Dispatch & Signal Preemption API
- Create a `POST /api/emergency/dispatch` endpoint that accepts a JSON payload: `{ "route": ["S34", "S22", ...] }`.
- When triggered, spawn an emergency vehicle that calculates its movement along this route.
- The simulation must inherently force the traffic signals on this sequence to `GREEN` as the vehicle approaches (Preemption).
- Include the emergency vehicle's [lat](file:///d:/signalIQ/signal-iq/components/SimulationOverlay.tsx#45-529)/`lng` position and status in the `/api/grid/state` polling response.

### 3. Machine Learning Congestion Prediction
- The frontend needs real AI forecasts. Implement a basic MVP ML model in Python (e.g., using `scikit-learn` or a simple regression script analyzing inflow rates, time-of-day, and current volume) to predict congestion 5 minutes into the future.
- Create a `GET /api/ml/predict` endpoint, or append an `aiPrediction` object to the nodes returned in the grid state loop.

Please review the backend codebase and begin implementing Phase 1 (Topographical Synchronization). Specifically, tell me what frontend data files you need me to provide so you can initialize the correct road network!
