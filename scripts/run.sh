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
  # Redirigimos stderr a /dev/null para ocultar el traceback de KeyboardInterrupt
  mp mount . run main.py 2>/dev/null || true
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
  mp run main.py || true
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
    0) rich_printer "[green]Saliendo.[/green]"; exit 0 ;;
    *) rich_printer "[yellow]Opción inválida.[/yellow]" ;;
  esac
  echo ""
done
