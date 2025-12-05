# Test script para verificar que el display funciona
import time
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import config

print("Inicializando hardware...")
time.sleep_ms(200)

# Inicializar I2C y OLED
i2c = I2C(0, scl=Pin(config.PIN_SCL), sda=Pin(config.PIN_SDA))
oled = SSD1306_I2C(config.OLED_WIDTH, config.OLED_HEIGHT, i2c)

print("Display inicializado")

# Limpiar pantalla
oled.fill(0)
oled.show()

# Mostrar texto de prueba
oled.text("TEST", 0, 0)
oled.text("Display OK", 0, 20)
oled.show()

print("Texto mostrado en display")

# Esperar un poco
time.sleep(2)

# Mostrar otro mensaje
oled.fill(0)
oled.text("Hello World!", 0, 0)
oled.text("Nomad Test", 0, 20)
oled.show()

print("Segundo mensaje mostrado")

