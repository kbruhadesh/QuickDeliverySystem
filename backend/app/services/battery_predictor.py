import pickle
import numpy as np
from typing import Dict
import os

class BatteryPredictor:
    def __init__(self, model_path='ml_models/battery_model.pkl'):
        # Allow relative paths when running directly from backend
        if not os.path.exists(model_path) and os.path.exists('../' + model_path):
            model_path = '../' + model_path
            
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
    
    def predict(self, distance_km: float, weight_kg: float, weather: Dict) -> float:
        """
        Predict battery consumption percentage
        
        Args:
            distance_km: Route distance in kilometers
            weight_kg: Package weight in kg
            weather: dict with keys: wind_speed, temperature, humidity
        
        Returns:
            Battery consumption percentage (0-100)
        """
        features = np.array([[
            distance_km,
            weight_kg,
            weather.get('wind_speed', 10),  # km/h
            weather.get('temperature', 25),  # Celsius
            weather.get('humidity', 60)  # percentage
        ]])
        
        prediction = self.model.predict(features)[0]
        
        # Apply weather penalties
        if weather.get('rain', 0) > 5:  # mm/hr
            prediction *= 1.2  # 20% penalty for rain
        
        if weather.get('wind_speed', 0) > 30:
            return 100  # Reject - too windy
        
        return min(prediction, 95)  # Cap at 95%
