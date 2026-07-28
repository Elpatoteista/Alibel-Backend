import requests
import json
import time
import random
import uuid

# User configuration
USER_ID = str(uuid.uuid4())
URL = "http://localhost:8000/api/sensor-data"

def generate_window(anomaly=False):
    # Simulated feature window
    # Features: [mean_accel_mag, var_accel_mag, max_accel_mag, mean_gyro_mag, var_gyro_mag, max_gyro_mag]
    if not anomaly:
        # Normal
        features = [
            random.gauss(9.8, 0.5),
            random.gauss(1.0, 0.5),
            random.gauss(11.0, 1.0),
            random.gauss(0.5, 0.2),
            random.gauss(0.1, 0.05),
            random.gauss(1.0, 0.5)
        ]
    else:
        # Anomaly
        features = [
            random.gauss(15.0, 5.0),
            random.gauss(50.0, 20.0),
            random.gauss(30.0, 10.0),
            random.gauss(5.0, 2.0),
            random.gauss(10.0, 5.0),
            random.gauss(15.0, 5.0)
        ]
    return features

def run_simulation():
    print(f"Simulando dispositivo para el usuario {USER_ID}")
    
    # 5 normales, 3 anómalos, luego normales
    states = [False]*5 + [True]*3 + [False]*5
    
    for i, is_anomaly in enumerate(states):
        window = generate_window(is_anomaly)
        
        payload = {
            "user_id": USER_ID,
            "features": window,
            "timestamp": time.time()
        }
        
        try:
            print(f"Enviando ventana {i} (Anomalía: {is_anomaly})...")
            response = requests.post(URL, json=payload)
            print(f"Respuesta: {response.status_code} - {response.json()}")
        except Exception as e:
            print(f"Error conectando al servidor: {e}")
            
        time.sleep(2) # Send faster than 5s for testing

if __name__ == "__main__":
    run_simulation()
