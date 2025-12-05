#!/bin/zsh

set -euo pipefail

# --- Entorno y Configuración ---
if [[ -f .venv/bin/activate ]]; then
  source .venv/bin/activate
fi

PY=${PY:-python}
PORT=4000
if [[ -f wokwi.toml ]]; then
  maybe_port=$(grep 'rfc2217ServerPort' wokwi.toml | sed 's/.*= *//' | tr -d -c '0-9')
  if [[ -n ${maybe_port:-} ]]; then
    PORT="${maybe_port}"
  fi
fi
DEVICE=${DEVICE:-port:rfc2217://localhost:${PORT}}

# --- Funciones de Utilidad ---
function rich_printer() {
  $PY scripts/rich_printer.py "$@"
}

function mp() {
  $PY -m mpremote connect "$DEVICE" "$@"
}

function show_header() {
  rich_printer "[bold cyan]Nomad Runner[/bold cyan]  [green]Dispositivo:[/green] [yellow]${DEVICE}[/yellow]"
}

function check_connection() {
    echo -n "Intentando conectar con el dispositivo..."
    if [[ "$DEVICE" == port:rfc2217://* ]]; then
        HOSTPORT=${DEVICE#port:rfc2217://}
        HOST=${HOSTPORT%:*}; PORT=${HOSTPORT##*:}
        if ! nc -z "$HOST" "$PORT" 2>/dev/null; then
            echo "" # Nueva línea
            rich_printer "[bold red]Error: No se pudo conectar al puerto ${HOST}:${PORT}. ¿Está corriendo el simulador Wokwi?[/bold red]"
            return 1
        fi
    fi
    if ! mp eval "1" >/dev/null 2>&1; then
        echo "" # Nueva línea
        rich_printer "[bold red]Error: No se pudo establecer comunicación con el dispositivo. ¿Está ocupado o desconectado?[/bold red]"
        return 1
    fi
    echo -ne "\r\033[K"
    rich_printer "[green]✓ Conexión exitosa.[/green]"
    return 0
}

# --- Funciones de Menú ---
function _execute_mount_run() {
  rich_printer "[dim]Montando directorio y ejecutando main.py...[/dim]"
  rich_printer "[dim]Para salir, presioná Ctrl+C.[/dim]"
  rich_printer "[yellow]Nota: Los mensajes print() aparecen en la consola del simulador Wokwi, no aquí.[/yellow]"
  rich_printer "[dim]Revisá la pestaña del simulador para ver la salida del código.[/dim]"
  rich_printer "[yellow]⚠️  IMPORTANTE: Si ves errores de atributos faltantes (SONG_INTRO, LOGO_CYPHER, etc.),[/yellow]"
  rich_printer "[yellow]   ejecutá primero la opción 3 (Update flash) para copiar todos los archivos al dispositivo.[/yellow]"
  echo ""
  # Redirigimos stderr a /dev/null para ocultar el traceback de KeyboardInterrupt
  mp mount . run main.py
}

function _do_reset_internal() {
  # Versión interna y silenciosa del reset
  mp reset >/dev/null 2>&1 || true
}

function do_mount_run() {
  show_header
  echo ""
  rich_printer "[b]Opción 1: Mount & Run (iniciar por primera vez)[/b]"
  check_connection || return 1
  
  # Verificar si ssd1306.py está en el dispositivo
  rich_printer "[dim]Verificando archivos necesarios...[/dim]"
  if ! mp fs ls :ssd1306.py >/dev/null 2>&1; then
    rich_printer "[yellow]Advertencia: ssd1306.py no encontrado en el dispositivo.[/yellow]"
    rich_printer "[yellow]Es necesario copiar los archivos primero.[/yellow]"
    echo ""
    read "?¿Ejecutar update_device.sh ahora? (s/n): " response
    if [[ "$response" =~ ^[SsYy]$ ]]; then
      ./scripts/update_device.sh
      echo ""
      rich_printer "[green]Archivos copiados. Continuando con mount & run...[/green]"
    else
      rich_printer "[yellow]Saliendo. Ejecutá la opción 3 primero para copiar los archivos.[/yellow]"
      return 1
    fi
  fi
  
  _execute_mount_run
}

function do_hot_reload() {
  show_header
  echo ""
  rich_printer "[b]Opción 2: Recargar código (Hot-Reload)[/b]"
  check_connection || return 1

  rich_printer "[dim]Reiniciando dispositivo...[/dim]"
  _do_reset_internal

  rich_printer "[dim]Esperando al dispositivo (2s)...[/dim]"
  sleep 2

  # Verificamos la conexión de nuevo después del reinicio
  check_connection || return 1

  _execute_mount_run
}

function do_update_flash() {
  show_header
  echo ""
  rich_printer "[b]Opción 3: Update flash[/b]"
  # La verificación de conexión se hará dentro del script
  ./scripts/update_device.sh
}

function do_reset() {
  show_header
  echo ""
  rich_printer "[b]Opción 4: Soft Reset[/b]"
  check_connection || return 1
  rich_printer "[dim]Realizando soft reset...[/dim]"
  _do_reset_internal
  rich_printer "[green]✓ Dispositivo reiniciado.[/green]"
}

function do_ls() {
  show_header
  echo ""
  rich_printer "[b]Opción 5: Listar archivos[/b]"
  check_connection || return 1
  rich_printer "[dim]Archivos en el dispositivo:[/dim]"
  mp fs ls || rich_printer "[yellow]Advertencia: No se pudieron listar archivos.[/yellow]"
}

function do_run_flash() {
  show_header
  echo ""
  rich_printer "[b]Opción 6: Run desde flash[/b]"
  check_connection || return 1
  rich_printer "[dim]Ejecutando main.py desde flash...[/dim]"
  rich_printer "[yellow]Nota: Los mensajes print() aparecen en la consola del simulador Wokwi.[/yellow]"
  mp run main.py || true
}

function do_test_connection() {
  show_header
  echo ""
  rich_printer "[b]Opción 7: Test de conexión y display[/b]"
  check_connection || return 1
  
  # Verificar si ssd1306.py está en el dispositivo
  if ! mp fs ls :ssd1306.py >/dev/null 2>&1; then
    rich_printer "[yellow]ssd1306.py no encontrado. Copiando archivos necesarios...[/yellow]"
    mp fs cp ssd1306.py :ssd1306.py 2>/dev/null || {
      rich_printer "[red]Error: No se pudo copiar ssd1306.py[/red]"
      rich_printer "[yellow]Ejecutá la opción 3 (Update flash) primero.[/yellow]"
      return 1
    }
  fi
  
  rich_printer "[dim]Ejecutando test simple del display...[/dim]"
  mp run test_display.py || true
}

# --- Bucle Principal ---
while true; do
  show_header
  echo ""
  rich_printer "[b]Seleccioná una opción:[/b]"
  rich_printer "  [cyan]1)[/] Mount & Run (iniciar por primera vez)"
  rich_printer "  [cyan]2)[/] Recargar código (Hot-Reload)"
  rich_printer "  [cyan]3)[/] Update flash (actualizar memoria persistente)"
  rich_printer "  [cyan]4)[/] Soft Reset"
  rich_printer "  [cyan]5)[/] Listar archivos en dispositivo"
  rich_printer "  [cyan]6)[/] Run desde flash (ejecutar main.py)"
  rich_printer "  [cyan]7)[/] Test de conexión y display"
  rich_printer "  [cyan]0)[/] Salir"
  echo -n "> "
  read choice
  case ${choice:-} in
    1) do_mount_run ;;
    2) do_hot_reload ;;
    3) do_update_flash ;;
    4) do_reset ;;
    5) do_ls ;;
    6) do_run_flash ;;
    7) do_test_connection ;;
    0) rich_printer "[green]Saliendo.[/green]"; exit 0 ;;
    *) rich_printer "[yellow]Opción inválida.[/yellow]" ;;
  esac
  echo ""
done
