#!/bin/zsh

# Script to update the Wokwi MicroPython device

# 1. Copy all .py files to the device
for f in *.py; do
  echo "Copying $f to device..."
  mpremote connect port:rfc2217://localhost:4000 fs cp "$f" :/
  if [ $? -ne 0 ]; then
    echo "Error: Failed to copy $f. Aborting."
    exit 1
  fi
done

# 2. List files on the device to confirm copy
echo "\nFiles on device:"
mpremote connect port:rfc2217://localhost:4000 fs ls

# 3. Wake up the display and show a test message
echo "\nWaking up display..."
mpremote connect port:rfc2217://localhost:4000 exec "import ssd1306, machine; i2c=machine.I2C(0, scl=machine.Pin(22), sda=machine.Pin(21)); d=ssd1306.SSD1306_I2C(128,64,i2c); d.fill(0); d.text('NOMAD',0,0); d.show()"

# 4. Execute the main script
echo "\nExecuting main.py..."
mpremote connect port:rfc2217://localhost:4000 exec "import main"

echo "\nUpdate complete."