import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import pickle
import json
import os

def generate_synthetic_data(n_samples=1000):
    """
    Generate synthetic training data
    Features: distance, weight, wind_speed, temperature, humidity
    Target: battery_consumption_percentage
    """
    np.random.seed(42)
    
    data = {
        'distance_km': np.random.uniform(0.5, 15, n_samples),  # 0.5 to 15 km
        'payload_weight_kg': np.random.uniform(0.1, 5.0, n_samples),  # 0.1 to 5 kg
        'wind_speed_kmh': np.random.uniform(0, 40, n_samples),  # 0 to 40 km/h
        'temperature_c': np.random.uniform(-5, 45, n_samples),  # -5 to 45°C
        'humidity_percent': np.random.uniform(20, 100, n_samples),  # 20 to 100%
    }
    
    df = pd.DataFrame(data)
    
    # Physics-based battery consumption formula
    # Base: 2% per km
    # Weight penalty: +0.5% per kg
    # Wind penalty: +0.1% per km/h above 20
    # Temperature penalty: +0.2% if < 5°C or > 35°C
    # Humidity: minimal effect
    
    battery_consumption = (
        df['distance_km'] * 2.0 +  # Base consumption
        df['payload_weight_kg'] * 0.5 +  # Weight factor
        np.maximum(df['wind_speed_kmh'] - 20, 0) * 0.1 +  # Wind penalty
        ((df['temperature_c'] < 5) | (df['temperature_c'] > 35)) * 2.0 +  # Temp penalty
        np.random.normal(0, 1, n_samples)  # Random noise
    )
    
    df['battery_consumption_percent'] = np.clip(battery_consumption, 5, 95)
    
    return df

def train_model():
    print("Generating synthetic training data...")
    df = generate_synthetic_data(1000)
    
    # Ensure directory exists
    os.makedirs('ml_models', exist_ok=True)
    
    # Save sample data for reference
    df.head(100).to_csv('ml_models/sample_training_data.csv', index=False)
    
    # Features and target
    X = df[['distance_km', 'payload_weight_kg', 'wind_speed_kmh', 
            'temperature_c', 'humidity_percent']]
    y = df['battery_consumption_percent']
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print("Training Random Forest model...")
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    print(f"\nModel Performance:")
    print(f"RMSE: {rmse:.2f}%")
    print(f"R² Score: {r2:.4f}")
    print(f"Target: RMSE < 5% → {'✅ PASS' if rmse < 5 else '❌ FAIL'}")
    
    # Feature importance
    importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\nFeature Importance:")
    print(importance)
    
    # Save model
    with open('ml_models/battery_model.pkl', 'wb') as f:
        pickle.dump(model, f)
    
    # Save metadata
    metadata = {
        'rmse': float(rmse),
        'r2_score': float(r2),
        'features': X.columns.tolist(),
        'n_samples': len(df),
        'model_type': 'RandomForestRegressor',
        'trained_at': pd.Timestamp.now().isoformat()
    }
    
    with open('ml_models/model_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("\n✅ Model saved to ml_models/battery_model.pkl")
    return model, rmse, r2

if __name__ == "__main__":
    train_model()
