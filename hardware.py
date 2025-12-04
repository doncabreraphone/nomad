# hardware.py
# Propósito:  Abstracción del Hardware (HAL). Inicializa el oled, buzzer, touch_pad y ldr_sensor. Contiene funciones como read_touch(), play_tone() o read_light_sensor(). Así el juego no se preocupa por cómo funcionan los pines.

from machine import Pin, I2C, PWM
from ssd1306 import SSD1306_I2C
import config
import time

oled = None
buzzer = None
button_a = None
button_b = None

def init_hardware():
    global oled, buzzer, button_a, button_b
    
    # Pausa para estabilizar el hardware
    time.sleep_ms(200)
    
    # Inicializar I2C y OLED
    i2c = I2C(0, scl=Pin(config.PIN_SCL), sda=Pin(config.PIN_SDA))
    oled = SSD1306_I2C(config.OLED_WIDTH, config.OLED_HEIGHT, i2c)
    
    # Inicializar Buzzer
    # Forzamos duty 0 al inicio para evitar pitidos residuales
    buzzer_pin = Pin(config.PIN_BUZZER, Pin.OUT)
    buzzer = PWM(buzzer_pin)
    buzzer.duty(0)
    buzzer.duty_u16(0) # Por si acaso usa u16
    
    # Inicializar Botones (Pull-up: 1=Suelto, 0=Presionado)
    # Asegurarnos que el pin es correcto y el modo también
    try:
        button_a = Pin(config.PIN_BUTTON_A, Pin.IN, Pin.PULL_UP)
        button_b = Pin(config.PIN_BUTTON_B, Pin.IN, Pin.PULL_UP)
    except Exception as e:
        print(f"Error initializing buttons: {e}")
        button_a = None
        button_b = None
    
    return oled, buzzer, button_a, button_b
