#!/bin/zsh

set -euo pipefail

DEVICE=${DEVICE:-port:rfc2217://localhost:4000}
if [ $# -ge 1 ]; then
  DEVICE="$1"
fi

echo "Usando dispositivo: $DEVICE"

if [[ "$DEVICE" == port:rfc2217://* ]]; then
  HOSTPORT=${DEVICE#port:rfc2217://}
  HOST=${HOSTPORT%:*}
  PORT=${HOSTPORT##*:}
  echo "Verificando $HOST:$PORT..."
  if ! nc -z "$HOST" "$PORT" 2>/dev/null; then
    echo "Error: No se pudo conectar a $HOST:$PORT. ¿Está corriendo el simulador Wokwi?"
    exit 1
  fi
fi

echo "Realizando reset suave del dispositivo..."
if ! mpremote connect "$DEVICE" reset; then
  echo "Advertencia: Falló el reset. Continuando con la copia..."
fi

for f in *.py; do
  echo "Copiando $f al dispositivo..."
  if ! mpremote connect "$DEVICE" fs cp "$f" :/; then
    echo "Error: Falló la copia de $f. Abortando."
    exit 1
  fi
done

echo "\nArchivos en el dispositivo:"
mpremote connect "$DEVICE" fs ls || echo "Advertencia: No se pudieron listar archivos."

echo "\nDespertando pantalla..."
mpremote connect "$DEVICE" exec "import ssd1306, machine; i2c=machine.I2C(0, scl=machine.Pin(22), sda=machine.Pin(21)); d=ssd1306.SSD1306_I2C(128,64,i2c); d.fill(0); d.text('NOMAD',0,0); d.show()" || echo "Advertencia: No se pudo ejecutar la prueba de pantalla."

echo "\nEjecutando main.py..."
mpremote connect "$DEVICE" exec "import main" || echo "Advertencia: No se pudo ejecutar main.py."

echo "\nActualización completa."