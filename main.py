from machine import Pin, I2C, PWM # --- NUEVO: Añadimos PWM ---
from ssd1306 import SSD1306_I2C
import time

# Pausa para estabilizar el hardware del simulador
time.sleep_ms(200)

# --- Configuración Inicial ---
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
oled = SSD1306_I2C(128, 64, i2c)

# --- NUEVO: Configuración del Buzzer ---
# Definimos el pin que usaremos para el buzzer
buzzer_pin = Pin(25, Pin.OUT)
# Creamos el objeto PWM que nos permitirá generar tonos
buzzer = PWM(buzzer_pin)


# --- Definimos el Layout de la Pantalla ---
ZONA_JUEGO_ALTO = 48
TEXTO_Y_1 = ZONA_JUEGO_ALTO
TEXTO_Y_2 = ZONA_JUEGO_ALTO + 8

# --- Lógica Principal del Juego ---

# 1. Borramos toda la pantalla
oled.fill(0)

# 2. Dibujamos al personaje usando texto en la "Zona de Juego"
oled.text("O", 60, 20)

# 3. Escribimos el diálogo en la "Zona de Texto"
linea1 = "Cambiaso"
linea2 = "> Cruzar"

oled.text(linea1, 0, TEXTO_Y_1)
oled.text(linea2, 0, TEXTO_Y_2)

# 4. Mostramos todo en la pantalla
oled.show()

# --- NUEVO: Hacemos sonar un "beep" de inicio ---
# Usamos un bloque try/finally para asegurarnos de que el buzzer
# siempre se apague al final, incluso si hay un error.
try:
    # Tono 1: Un beep corto de bienvenida
    buzzer.freq(800)          # Frecuencia (tono)
    buzzer.duty_u16(32768)    # Volumen (50%)
    time.sleep_ms(100)        # Duración
    
    # Pausa silenciosa
    buzzer.duty_u16(0)        # Apagamos el volumen
    time.sleep_ms(50)
    
    # Tono 2: Un beep más agudo
    buzzer.freq(1200)
    buzzer.duty_u16(32768)
    time.sleep_ms(150)

finally:
    # --- NUEVO: Limpieza final ---
    # Es una buena práctica apagar y liberar el buzzer al final del script.
    buzzer.duty_u16(0)
    buzzer.deinit()