"""
Battery Prediction Service - Simplified physics-based model
Save as: backend/app/services/battery_predictor.py
"""

from typing import Dict, Optional


class BatteryPredictor:
    """
    Battery consumption predictor for drone delivery
    Uses physics-based formulas instead of ML (can be upgraded to ML later)
    """
    
    def __init__(self):
        # Base consumption rate: 2% battery per km
        self.base_rate = 2.0  # % per km
        
        # Weight penalty: 0.5% per kg of payload
        self.weight_factor = 0.5  # % per kg per km
        
        # Wind penalty: 0.1% per km/h of headwind above 20 km/h
        self.wind_threshold = 20.0  # km/h
        self.wind_factor = 0.1  # % per km/h
        
        # Temperature penalties
        self.cold_temp_threshold = 5.0  # Celsius
        self.hot_temp_threshold = 35.0  # Celsius
        self.temp_penalty = 2.0  # % per km
        
        # Rain penalty
        self.rain_penalty_factor = 1.2  # 20% increase
    
    def predict_simple(
        self,
        distance_km: float,
        weight_kg: float = 0.0
    ) -> float:
        """
        Simple battery prediction based only on distance and weight
        
        Args:
            distance_km: Total route distance in kilometers
            weight_kg: Package weight in kilograms
        
        Returns:
            Predicted battery consumption in percentage (0-100)
        """
        # Base consumption
        consumption = distance_km * self.base_rate
        
        # Add weight penalty
        consumption += distance_km * weight_kg * self.weight_factor
        
        # Add 10% buffer for safety
        consumption *= 1.1
        
        # Cap at 95% (never predict full battery drain)
        return min(consumption, 95.0)
    
    def predict(
        self,
        distance_km: float,
        weight_kg: float = 0.0,
        weather: Optional[Dict] = None
    ) -> float:
        """
        Advanced battery prediction with weather factors
        
        Args:
            distance_km: Total route distance in kilometers
            weight_kg: Package weight in kilograms
            weather: Dictionary with weather data
                - wind_speed: Wind speed in km/h
                - temperature: Temperature in Celsius
                - precipitation: Rain in mm/h
                - conditions: Weather condition string
        
        Returns:
            Predicted battery consumption in percentage (0-100)
        """
        # Start with simple prediction
        consumption = distance_km * self.base_rate
        
        # Add weight penalty
        consumption += distance_km * weight_kg * self.weight_factor
        
        # Apply weather factors if available
        if weather:
            # Wind penalty
            wind_speed = weather.get('wind_speed', 0)
            if wind_speed > self.wind_threshold:
                excess_wind = wind_speed - self.wind_threshold
                consumption += distance_km * excess_wind * self.wind_factor
            
            # Temperature penalty
            temperature = weather.get('temperature', 25)
            if temperature < self.cold_temp_threshold or temperature > self.hot_temp_threshold:
                consumption += distance_km * self.temp_penalty
            
            # Rain penalty
            precipitation = weather.get('precipitation', 0)
            if precipitation > 0:
                consumption *= self.rain_penalty_factor
            
            # Extreme conditions check
            if wind_speed > 40:
                return 100.0  # Too windy to fly
            
            if precipitation > 10:
                return 100.0  # Too much rain
        
        # Add 10% safety buffer
        consumption *= 1.1
        
        # Cap at 95%
        return min(consumption, 95.0)
    
    def can_complete_delivery(
        self,
        current_battery: float,
        distance_km: float,
        weight_kg: float = 0.0,
        weather: Optional[Dict] = None,
        safety_margin: float = 20.0
    ) -> Dict:
        """
        Check if drone has enough battery to complete delivery
        
        Args:
            current_battery: Current battery percentage
            distance_km: Route distance
            weight_kg: Package weight
            weather: Weather data
            safety_margin: Minimum battery % to keep in reserve
        
        Returns:
            Dictionary with:
                - can_complete: Boolean
                - predicted_consumption: Battery % needed
                - remaining_battery: Battery % after delivery
                - reason: Explanation if cannot complete
        """
        predicted = self.predict(distance_km, weight_kg, weather)
        required = predicted + safety_margin
        
        can_complete = current_battery >= required
        remaining = current_battery - predicted
        
        reason = None
        if not can_complete:
            if current_battery < predicted:
                reason = f"Insufficient battery: need {predicted:.1f}%, have {current_battery:.1f}%"
            else:
                reason = f"Would leave only {remaining:.1f}% battery (need {safety_margin:.1f}% safety margin)"
        
        return {
            'can_complete': can_complete,
            'predicted_consumption': predicted,
            'remaining_battery': remaining,
            'required_battery': required,
            'reason': reason
        }
    
    def estimate_range(
        self,
        current_battery: float,
        weight_kg: float = 0.0,
        weather: Optional[Dict] = None
    ) -> float:
        """
        Estimate maximum range with current battery
        
        Returns:
            Maximum distance in kilometers
        """
        # Keep 20% safety margin
        usable_battery = current_battery - 20.0
        
        if usable_battery <= 0:
            return 0.0
        
        # Calculate base range
        base_consumption_per_km = self.base_rate + (weight_kg * self.weight_factor)
        
        # Apply weather factors
        if weather:
            wind_speed = weather.get('wind_speed', 0)
            if wind_speed > self.wind_threshold:
                excess_wind = wind_speed - self.wind_threshold
                base_consumption_per_km += excess_wind * self.wind_factor
            
            temperature = weather.get('temperature', 25)
            if temperature < self.cold_temp_threshold or temperature > self.hot_temp_threshold:
                base_consumption_per_km += self.temp_penalty
            
            precipitation = weather.get('precipitation', 0)
            if precipitation > 0:
                base_consumption_per_km *= self.rain_penalty_factor
        
        # Add safety buffer
        base_consumption_per_km *= 1.1
        
        # Calculate max range
        max_range = usable_battery / base_consumption_per_km
        
        return max_range


# Example usage and testing
if __name__ == "__main__":
    predictor = BatteryPredictor()
    
    # Test simple prediction
    print("Simple Prediction Tests:")
    print(f"5 km, 0 kg: {predictor.predict_simple(5, 0):.2f}%")
    print(f"10 km, 2 kg: {predictor.predict_simple(10, 2):.2f}%")
    print(f"15 km, 5 kg: {predictor.predict_simple(15, 5):.2f}%")
    
    # Test with weather
    print("\nWeather-aware Prediction:")
    weather_good = {
        'wind_speed': 10,
        'temperature': 25,
        'precipitation': 0
    }
    print(f"10 km, 2 kg, good weather: {predictor.predict(10, 2, weather_good):.2f}%")
    
    weather_bad = {
        'wind_speed': 35,
        'temperature': 5,
        'precipitation': 3
    }
    print(f"10 km, 2 kg, bad weather: {predictor.predict(10, 2, weather_bad):.2f}%")
    
    # Test completion check
    print("\nCompletion Check:")
    result = predictor.can_complete_delivery(
        current_battery=80,
        distance_km=10,
        weight_kg=2,
        weather=weather_good
    )
    print(f"Can complete: {result['can_complete']}")
    print(f"Predicted consumption: {result['predicted_consumption']:.2f}%")
    print(f"Remaining after: {result['remaining_battery']:.2f}%")
    
    # Test range estimation
    print("\nRange Estimation:")
    max_range = predictor.estimate_range(80, 2, weather_good)
    print(f"Max range with 80% battery, 2kg load: {max_range:.2f} km")
