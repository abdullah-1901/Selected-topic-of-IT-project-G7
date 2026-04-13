ID_SCOPE = "0ne01050752"
DEVICE_ID = "G7"
PRIMARY_KEY = "qLv1zz9pK9m4sf15ogaefDce7o5Ai7v/HCI5rF8cSz4="

import time
import json
import serial
import requests
from azure.iot.device import IoTHubDeviceClient, ProvisioningDeviceClient, Message

# ==========================================
# 1. SETUP YOUR VARIABLES HERE
# ==========================================

# IoT Central Credentials
ID_SCOPE = "0ne01050752"
DEVICE_ID = "G7"
PRIMARY_KEY = "qLv1zz9pK9m4sf15ogaefDce7o5Ai7v/HCI5rF8cSz4="

# Azure Machine Learning Credentials
ML_URL = "https://air-quality-g7-final.qatarcentral.inference.ml.azure.com/score"
ML_KEY = "DkHVJNuhqvsso3v4k6KTSPgSzfegY54hD7tUshnXwkYLmXQd2KeBJQQJ99CDAAAAAAAAAAAAINFRAZML10DH"

# Arduino Serial Settings
SERIAL_PORT = "COM3"   # change if needed
BAUD_RATE = 9600

# ==========================================
# 2. CONNECT TO AZURE IOT CENTRAL
# ==========================================
def connect_to_azure():
    print("Provisioning device...")
    provisioning_client = ProvisioningDeviceClient.create_from_symmetric_key(
        provisioning_host="global.azure-devices-provisioning.net",
        registration_id=DEVICE_ID,
        id_scope=ID_SCOPE,
        symmetric_key=PRIMARY_KEY
    )

    registration_result = provisioning_client.register()

    if registration_result.status != "assigned":
        raise Exception("Device provisioning failed")

    print("Connecting to IoT Central...")
    client = IoTHubDeviceClient.create_from_symmetric_key(
        symmetric_key=PRIMARY_KEY,
        hostname=registration_result.registration_state.assigned_hub,
        device_id=DEVICE_ID
    )

    client.connect()
    print("Connected to IoT Central successfully!\n")
    return client

# ==========================================
# 3. CONNECT TO ARDUINO
# ==========================================
def connect_to_arduino():
    print("Connecting to Arduino...")
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
    time.sleep(2)
    print("Connected to Arduino successfully!\n")
    return ser

# ==========================================
# 4. CLEAN SERIAL DATA
# Supports:
#    29
#    AQI Value: 29
# ==========================================
def parse_arduino_value(raw_value):
    raw_value = raw_value.strip()

    if not raw_value:
        return None

    if ":" in raw_value:
        raw_value = raw_value.split(":")[-1].strip()

    return int(raw_value)

# ==========================================
# 5. SEND REAL DATA TO IOT + CALL ML
# ==========================================
def main():
    azure_client = connect_to_azure()
    ser = connect_to_arduino()

    print("Starting process: Real Arduino data -> IoT Central + ML Endpoint\n")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ML_KEY}"
    }

    try:
        while True:
            raw_serial = ser.readline().decode("utf-8", errors="ignore").strip()

            if not raw_serial:
                continue

            try:
                aqi_value = parse_arduino_value(raw_serial)

                if aqi_value is None:
                    continue

                # ------------------------------------------
                # 1) Send real AQI data to IoT Central
                # ------------------------------------------
                iot_payload = {"AQI": aqi_value}
                msg = Message(json.dumps(iot_payload))
                msg.content_encoding = "utf-8"
                msg.content_type = "application/json"

                azure_client.send_message(msg)
                print(f"-> Sent to IoT Central: {iot_payload}")

                # ------------------------------------------
                # 2) Call ML endpoint for prediction
                # Adjust payload if your endpoint expects
                # something different
                # ------------------------------------------
                ml_payload = {"AQI": aqi_value}

                try:
                    response = requests.post(
                        ML_URL,
                        headers=headers,
                        json=ml_payload,
                        timeout=15
                    )

                    if response.status_code == 200:
                        try:
                            prediction = response.json()
                        except Exception:
                            prediction = response.text

                        print(f"<- ML Prediction Received: {prediction}\n")

                    else:
                        print(f"<- ML Error ({response.status_code}): {response.text}\n")

                except Exception as e:
                    print(f"<- Failed to reach ML endpoint: {e}\n")

                # send every 10 seconds
                time.sleep(10)

            except ValueError:
                print(f"Invalid Arduino data: {raw_serial}\n")

    except KeyboardInterrupt:
        print("\nStopping script...")

    finally:
        ser.close()
        azure_client.disconnect()

if __name__ == "__main__":
    main()
