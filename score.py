import json
import os
import sys
import subprocess


subprocess.check_call([sys.executable, "-m", "pip", "install", "statsmodels"])

import joblib

def init():
    global model

    model_path = os.path.join(
        os.getenv("AZUREML_MODEL_DIR"),
        "aqi_model.pkl"
    )

    model = joblib.load(model_path)

def run(raw_data):
    data = json.loads(raw_data)

    steps = data.get("steps", 10)

    prediction = model.forecast(steps=steps)

    return prediction.tolist()