# hq_scene.py
# Propósito: La base de operaciones (Headquarters). Desde aquí se lanzan misiones, se ve el estado, etc.

import time

def play_scene(oled):
    oled.fill(0)
    oled.text("HQ SCENE", 30, 25)
    oled.text("Coming Soon...", 10, 40)
    oled.show()
    
    # Pausa para ver el mensaje
    time.sleep(2)
