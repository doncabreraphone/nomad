# Test script para verificar FONT_BOLD
import time
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import config
import fonts

print("Inicializando hardware...")
time.sleep_ms(200)

# Inicializar I2C y OLED
i2c = I2C(0, scl=Pin(config.PIN_SCL), sda=Pin(config.PIN_SDA))
oled = SSD1306_I2C(config.OLED_WIDTH, config.OLED_HEIGHT, i2c)

print("Display inicializado")
print(f"FONT_BOLD_HEIGHT: {fonts.FONT_BOLD_HEIGHT}")

# Test 1: Texto simple
oled.fill(0)
fonts.draw(oled, "Launch", 0, 0, font_data=fonts.FONT_BOLD, color=1)
oled.show()
print("Test 1: 'Launch' en blanco sobre negro")
time.sleep(2)

# Test 2: Texto negro sobre fondo blanco (como en el menú)
oled.fill(1)  # Fondo blanco
fonts.draw(oled, "Launch", 0, 0, font_data=fonts.FONT_BOLD, color=0)
oled.show()
print("Test 2: 'Launch' en negro sobre blanco")
time.sleep(2)

# Test 3: Todos los caracteres
oled.fill(0)
test_text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
y = 0
for i in range(0, len(test_text), 16):
    line = test_text[i:i+16]
    fonts.draw(oled, line, 0, y, font_data=fonts.FONT_BOLD, color=1)
    y += fonts.FONT_BOLD_HEIGHT + 2
    if y > 64:
        break
oled.show()
print("Test 3: Alfanumérico completo")
time.sleep(3)

print("Tests completados")

