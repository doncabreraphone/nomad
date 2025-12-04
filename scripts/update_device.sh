#!/bin/zsh

set -euo pipefail

# --- Entorno y Wrapper mpremote ---
if [[ -f .venv/bin/activate ]]; then
  source .venv/bin/activate
fi

PY=${PY:-python}

function rich_printer() {
  $PY scripts/rich_printer.py "$@"
}

DEVICE=${DEVICE:-port:rfc2217://localhost:4000}
if [ $# -ge 1 ]; then
  DEVICE="$1"
fi

function mp() {
  $PY -m mpremote connect "$DEVICE" "$@"
}

function check_connection() {
  rich_printer "[dim]Verificando conexión con $DEVICE...[/dim]"
  if ! mp ls >/dev/null 2>&1; then
    rich_printer "[bold red]Error: No se puede conectar con el dispositivo en $DEVICE.[/bold red]"
    rich_printer "[yellow]Sugerencias:[/yellow]"
    rich_printer "  - Asegúrate de que el simulador Wokwi esté corriendo (F1 -> Start Simulator)."
    rich_printer "  - Verifica que el puerto sea correcto (por defecto localhost:4000)."
    exit 1
  fi
}

# --- Barra de Progreso ---
function progress_bar() {
  local total=$1
  local current=$2
  local width=50
  local percent=$((current * 100 / total))
  local completed_width=$((width * percent / 100))
  
  local bar="["
  for i in $(seq 1 $completed_width); do bar+="="; done
  for i in $(seq $completed_width $(($width - 1))); do bar+=" "; done
  bar+="]"
  
  # Usar echo -ne para la barra de progreso para que se actualice en una línea
  echo -ne "  $bar ${percent}%% (${current}/${total})\r"
  
  if [[ $current -eq $total ]]; then
    echo "" # Línea nueva al completar
  fi
}

# --- Lógica Principal ---
rich_printer "[bold cyan]Iniciando actualización para:[/] [yellow]${DEVICE}[/yellow]"

# 1. Conectar y preparar
echo ""
rich_printer "[b]Paso 1: Conectando y preparando el dispositivo...[/b]"
check_connection

rich_printer "[dim]Intentando interrumpir cualquier script (Ctrl+C)...[/dim]"
mp repl -c "import os; os.write(0, b'\x03')" >/dev/null 2>&1 || true
sleep 0.5

rich_printer "[dim]Intentando un soft reset...[/dim]"
if ! mp reset >/dev/null 2>&1; then
  rich_printer "[yellow]El soft reset inicial falló. Reintentando...[/yellow]"
  sleep 1
  if ! mp reset >/dev/null 2>&1; then
    rich_printer "[bold red]Error: No se pudo resetear el dispositivo. Abortando.[/bold red]"
    exit 1
  fi
fi
rich_printer "[green]✓ Dispositivo listo.[/green]"

# 2. Obtener listas de archivos
echo ""
rich_printer "[b]Paso 2: Comparando archivos locales y remotos...[/b]"
device_files_raw=$(mp fs ls 2>/dev/null || true)
local_py_files=($(ls *.py))
remote_py_files=()
for line in ${(f)device_files_raw}; do
  name=$(echo "$line" | awk '{print $2}')
  if [[ -n "$name" && "$name" != */ && "$name" == *.py ]]; then
    remote_py_files+=("$name")
  fi
done
rich_printer "[green]✓ Listas de archivos generadas.[/green]"

# 3. Borrar archivos obsoletos
to_delete=()
for r_file in "${remote_py_files[@]}"; do
  if ! (echo "${local_py_files[@]}" | grep -q -w "$r_file"); then
    to_delete+=("$r_file")
  fi
done

if [ ${#to_delete[@]} -gt 0 ]; then
  echo ""
  rich_printer "[b]Paso 3: Eliminando archivos obsoletos...[/b]"
  i=0; total=${#to_delete[@]}
  for file in "${to_delete[@]}"; do
    i=$((i + 1)); progress_bar $total $i
    mp fs rm ":/$file" >/dev/null 2>&1
  done
  rich_printer "[green]✓ ${total} archivos eliminados.[/green]"
else
  echo ""
  rich_printer "[b]Paso 3: Eliminando archivos obsoletos...[/b] [dim]Nada que eliminar.[/dim]"
fi

# 4. Copiar archivos
echo ""
rich_printer "[b]Paso 4: Copiando archivos del proyecto...[/b]"

# Copiar archivos python de la raíz
total=${#local_py_files[@]}
rich_printer "[dim]Copiando ${total} archivos de raíz...[/dim]"
for file in "${local_py_files[@]}"; do
  rich_printer "[dim]  - ${file}[/dim]"
  mp fs cp "$file" :/ >/dev/null 2>&1
done

# Copiar estructura de directorios (menus/)
rich_printer "[dim]Copiando carpetas...[/dim]"
# Asegurar que existe el directorio 'menus'
mp fs mkdir :menus >/dev/null 2>&1 || true
# Copiar archivos dentro de menus/
for file in menus/*.py; do
  if [[ -f "$file" ]]; then
    rich_printer "[dim]  - ${file}[/dim]"
    mp fs cp "$file" :menus/ >/dev/null 2>&1
  fi
done

rich_printer "[green]✓ Archivos copiados.[/green]"

# 5. Reset final
echo ""
rich_printer "[b]Paso 5: Reiniciando dispositivo...[/b]"
if ! mp reset >/dev/null 2>&1; then
  rich_printer "[yellow]Advertencia: El reinicio final falló.[/yellow]"
else
  rich_printer "[green]✓ Dispositivo reiniciado.[/green]"
fi

echo ""
rich_printer "[bold green]✨ Actualización completada con éxito ✨[/bold green]"
