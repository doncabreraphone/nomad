#!/bin/zsh

set -euo pipefail

# --- Configuración del Entorno ---

# Activar el entorno virtual de Python
source .venv/bin/activate

# Alias para el printer de Rich
RICH_PRINTER="python3 scripts/rich_printer.py"

# --- Detección del Dispositivo ---

DEVICE=${DEVICE:-port:rfc2217://localhost:4000}
if [ $# -ge 1 ]; then
  DEVICE="$1"
fi

$RICH_PRINTER "[bold cyan]Usando dispositivo:[/] [yellow]${DEVICE}[/yellow]"

# --- Verificación de Conexión (para simulador) ---

if [[ "$DEVICE" == port:rfc2217://* ]]; then
  HOSTPORT=${DEVICE#port:rfc2217://}
  HOST=${HOSTPORT%:*}
  PORT=${HOSTPORT##*:}
  $RICH_PRINTER "[blue]Verificando conexión con ${HOST}:${PORT}...[/blue]"
  if ! nc -z "$HOST" "$PORT" 2>/dev/null; then
    $RICH_PRINTER "[bold red]Error: No se pudo conectar a ${HOST}:${PORT}. ¿Está corriendo el simulador Wokwi?[/bold red]"
    exit 1
  fi
fi

# --- Proceso de Carga ---

$RICH_PRINTER "[blue]Realizando reset suave del dispositivo...[/blue]"
if ! mpremote connect "$DEVICE" reset; then
  $RICH_PRINTER "[yellow]Advertencia: Falló el reset. Continuando de todas formas...[/yellow]"
fi

# Array para almacenar el estado de los archivos
declare -a file_statuses

for f in *.py; do
  if mpremote connect "$DEVICE" fs cp "$f" :/; then
    file_statuses+=("$f" "[bold green]✓ Copiado[/bold green]")
  else
    file_statuses+=("$f" "[bold red]✗ Falló[/bold red]")
  fi
done

# Imprimir la tabla de estado de archivos
$RICH_PRINTER table "${file_statuses[@]}"

$RICH_PRINTER "\n[bold cyan]Archivos en el dispositivo:[/bold cyan]"
mpremote connect "$DEVICE" fs ls || $RICH_PRINTER "[yellow]Advertencia: No se pudieron listar archivos.[/yellow]"

$RICH_PRINTER "\n[bold cyan]Despertando pantalla...[/bold cyan]"
mpremote connect "$DEVICE" exec "import ssd1306, machine; i2c=machine.I2C(0, scl=machine.Pin(22), sda=machine.Pin(21)); d=ssd1306.SSD1306_I2C(128,64,i2c); d.fill(0); d.text('NOMAD',0,0); d.show()" || $RICH_PRINTER "[yellow]Advertencia: No se pudo ejecutar la prueba de pantalla.[/yellow]"

$RICH_PRINTER "\n[bold cyan]Ejecutando main.py...[/bold cyan]"
mpremote connect "$DEVICE" exec "import main" || $RICH_PRINTER "[yellow]Advertencia: No se pudo ejecutar main.py.[/yellow]"

$RICH_PRINTER "\n[bold green]✨ Actualización completa ✨[/bold green]"