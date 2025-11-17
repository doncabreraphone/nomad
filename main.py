# main.py

from machine import Pin, I2C, PWM
from ssd1306 import SSD1306_I2C
import time
# --- NUEVO: Importamos la librería para manejar los gráficos ---
import framebuf

# --- ASSETS ---
# Importamos el módulo que contiene nuestra animación
import test_animation
import music_intro
import _thread
from sound_manager import load_song, play_music_loop

# --- Configuración Inicial ---
# Pausa para estabilizar el hardware del simulador
time.sleep_ms(200)

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
oled = SSD1306_I2C(128, 64, i2c)

buzzer_pin = Pin(25, Pin.OUT)
buzzer = PWM(buzzer_pin)

# --- NUEVO: Preparación de la Animación ---
# Convertimos cada bytearray de nuestros assets en un objeto de imagen
anim_fb = []
for frame_data in test_animation.TEST_ANIMATION:
    fb = framebuf.FrameBuffer(frame_data, 128, 64, framebuf.MONO_HLSB)
    anim_fb.append(fb)

# --- Tareas en Segundo Plano ---
# Cargamos la canción que queremos reproducir
load_song(music_intro)

# Iniciamos la música en un hilo separado para que no bloquee la animación
_thread.start_new_thread(play_music_loop, (buzzer,))

# --- BUCLE PRINCIPAL DE ANIMACIÓN (REEMPLAZA EL CÓDIGO ANTERIOR) ---
frame_actual = 0
# Velocidad de 8 FPS (1000ms / 8 = 125ms por fotograma)
velocidad_anim_ms = 125 

print("Starting main animation loop...")
while True:
    # 1. Obtenemos el FrameBuffer del fotograma actual
    frame_a_dibujar = anim_fb[frame_actual]
    
    # 2. Borramos la pantalla y dibujamos el fotograma en la posición (0, 0)
    oled.fill(0)
    oled.blit(frame_a_dibujar, 0, 0)
    
    # 3. Mostramos el resultado
    oled.show()
    
    # 4. Avanzamos al siguiente fotograma
    frame_actual = (frame_actual + 1) % len(anim_fb)
    
    # 5. Esperamos para controlar la velocidad de la animación
    time.sleep_ms(velocidad_anim_ms)