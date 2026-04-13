import serial
import time

# change COM port if needed (e.g. COM3, COM6, etc.)
ser = serial.Serial('COM3', 9600)

time.sleep(2)  # wait for connection to initialize

print("Reading data from Arduino...\n")

while True:
    try:
        data = ser.readline().decode('utf-8').strip()
        if data:
            print("AQI:", data)
    except:
        print("Error reading data")
