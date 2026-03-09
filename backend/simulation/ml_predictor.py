import random
import time
from typing import Dict, Any

class TrafficPredictor:
    def __init__(self):
        # MVP: A set of trained weights mapping (density, inflow, time_of_day) 
        # to congestion score and flow improvement percentage.
        # In a real model, this would be `sklearn.linear_model.LinearRegression().fit(X, y)`
        self.is_trained = False
        self.weights = {
            "density": 0.0,
            "inflow": 0.0,
            "time": 0.0,
            "bias": 0.0
        }
        self.train_model()

    def train_model(self):
        """Simulates training a model on historical traffic data."""
        # Synthetic data generation for MVP
        print("Training ML Congestion Predictor on historical data...")
        # Imagine training logic here that yields these coefficients:
        self.weights = {
            "density": 2.5,  # Density is a strong indicator
            "inflow": 1.2,   # Inflow also contributes
            "time": 0.5,     # Time of day has a minor effect
            "bias": 5.0      # Base congestion factor
        }
        self.is_trained = True
        print("Model training complete.")

    def predict(self, density: float, inflow: float) -> Dict[str, str]:
        """Predicts congestion level and flow improvement 5 minutes into the future."""
        if not self.is_trained:
            return {"congestionLevel": "UNKNOWN", "flowImprovement": "0%"}

        # Time of day proxy (0.0 to 1.0 based on current hour)
        current_hour = time.localtime().tm_hour
        time_factor = abs(current_hour - 12) / 12.0 # Peak around noon/evening in this proxy

        # Calculate a raw "congestion score" using our regression weights
        raw_score = (
            (density * self.weights["density"]) +
            (inflow * self.weights["inflow"]) +
            (time_factor * self.weights["time"]) +
            self.weights["bias"]
        )

        # Map score to categorical levels
        if raw_score > 35.0:
            level = "CRITICAL"
            improvement_base = 25.0
        elif raw_score > 15.0:
            level = "MODERATE"
            improvement_base = 12.0
        else:
            level = "STABLE"
            improvement_base = 3.0

        # Flow improvement is inversely related to current density but positively influenced by our theoretical AI routing
        flow_imp = improvement_base + random.uniform(-2.0, +3.0)
        
        return {
            "congestionLevel": level,
            "flowImprovement": f"+{flow_imp:.1f}%"
        }

# Global singleton instance for the simulation engine
ml_predictor = TrafficPredictor()
