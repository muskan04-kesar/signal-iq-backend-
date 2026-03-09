# Phase 3 Backend Prompt
*Copy and paste the text below directly into the chat with the Backend Agent to begin the Machine Learning phase.*

***

Excellent work on Phase 2! The Emergency Dispatch API and dynamic signal preemption physics are functioning perfectly on the geographic graph. The frontend is rendering the ambulance and the forced-green routing flawlessly.

Now it is time to move on to our final MVP objective, **Phase 3: Machine Learning Congestion Prediction.**

Currently, the frontend's AI Prediction HUD is faking its data based on a simple density math formula. We need real machine learning forecasts coming from your application.

### Phase 3 EPIC: Machine Learning Congestion Forecasting
- Implement a basic MVP ML model in Python within the FastAPI service.
- You can use libraries like `scikit-learn` (or a simple linear/polynomial regression script if you want to keep dependencies light for the MVP).
- **The Goal**: Analyze current traffic simulator parameters (e.g., node inflow rates, current density/volume, time-of-day proxies) to predict congestion metrics **5 minutes into the future**.
- **The Output**: Expose this either via a dedicated `GET /api/ml/predict` endpoint, OR append an `aiPrediction` object to the nodes returned in the existing `/api/grid/state` loop. The frontend expects a payload structure resembling this for the HUD:
  ```json
  "aiPrediction": {
    "congestionLevel": "CRITICAL", // STABLE, MODERATE, CRITICAL
    "flowImprovement": "+14%"      // Estimated improvement metric
  }
  ```

Please let me know your plan for building this ML model and how you intend to train/evaluate it dynamically against the running simulation data!
