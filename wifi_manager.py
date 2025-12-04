# wifi_manager.py
# Propósito: Maneja la conexión WiFi y el Uplink.

import time

def connect():
    print("Connecting to WiFi...")
    time.sleep(1)
    print("Connected (Simulation).")

def play_scene(oled):
    oled.fill(0)
    oled.text("UPLINK MODE", 20, 25)
    oled.text("Searching...", 20, 40)
    oled.show()
    time.sleep(2)
