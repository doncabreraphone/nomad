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
  
  # Batch delete
  BATCH_SIZE=10
  TOTAL=${#to_delete[@]}
  for ((i=0; i<TOTAL; i+=BATCH_SIZE)); do
    CMD_ARGS=()
    # Add commands
    for ((j=i; j<i+BATCH_SIZE && j<TOTAL; j++)); do
        if [ ${#CMD_ARGS[@]} -gt 0 ]; then CMD_ARGS+=("+"); fi
        CMD_ARGS+=("fs" "rm" ":/${to_delete[j]}")
    done
    progress_bar $TOTAL $j
    mp "${CMD_ARGS[@]}" >/dev/null 2>&1
  done
  rich_printer "[green]✓ ${TOTAL} archivos eliminados.[/green]"
else
  echo ""
  rich_printer "[b]Paso 3: Eliminando archivos obsoletos...[/b] [dim]Nada que eliminar.[/dim]"
fi

# 4. Copiar archivos
echo ""
rich_printer "[b]Paso 4: Copiando archivos del proyecto...[/b]"

# Recolectar operaciones de copia
COPY_OPS=()

# Archivos raíz
for file in "${local_py_files[@]}"; do
    COPY_OPS+=("$file")
    COPY_OPS+=(":/${file}")
done

# Archivos de menús
# Asegurar directorio (rápido, una sola llamada)
mp fs mkdir :menus >/dev/null 2>&1 || true

for file in menus/*.py; do
  if [[ -f "$file" ]]; then
    base=$(basename "$file")
    COPY_OPS+=("$file")
    COPY_OPS+=(":menus/$base")
  fi
done

# Total de pares
TOTAL_OPS=$((${#COPY_OPS[@]} / 2))
rich_printer "[dim]Copiando ${TOTAL_OPS} archivos en lotes (optimizado)...[/dim]"

# Procesar en lotes
# En Zsh los arrays son 1-based.
# COPY_OPS tiene [src1, dst1, src2, dst2, ...]
# Indices: 1, 2, 3, 4, ...

FILES_PER_BATCH=10
BATCH_STEP=$((FILES_PER_BATCH * 2))

# Iterar i desde 1, saltando de a BATCH_STEP
# El limite es el tamaño del array
ARRAY_LEN=${#COPY_OPS[@]}

copied_count=0
batch_num=0
for ((i=1; i<=ARRAY_LEN; i+=BATCH_STEP)); do
    batch_num=$((batch_num + 1))
    CMD_ARGS=()
    files_in_this_batch=0
    
    # Construir comando mpremote batch
    # Sub-bucle para recoger elementos del lote
    # j va desde i hasta i + BATCH_STEP - 1
    for ((j=i; j<i+BATCH_STEP && j<=ARRAY_LEN; j+=2)); do
        src="${COPY_OPS[j]}"
        dst="${COPY_OPS[j+1]}"
        
        if [ ${#CMD_ARGS[@]} -gt 0 ]; then CMD_ARGS+=("+"); fi
        CMD_ARGS+=("fs" "cp" "$src" "$dst")
        files_in_this_batch=$((files_in_this_batch + 1))
    done
    
    # Ejecutar batch (silenciosamente, solo mostrar errores)
    if mp "${CMD_ARGS[@]}" >/dev/null 2>&1; then
        copied_count=$((copied_count + files_in_this_batch))
    else
        # Si falla el batch, intentar copiar archivo por archivo para identificar el problema
        for ((j=i; j<i+BATCH_STEP && j<=ARRAY_LEN; j+=2)); do
            src="${COPY_OPS[j]}"
            dst="${COPY_OPS[j+1]}"
            if mp fs cp "$src" "$dst" >/dev/null 2>&1; then
                copied_count=$((copied_count + 1))
            else
                rich_printer "[yellow]Advertencia: Error al copiar $(basename "$src")[/yellow]"
            fi
        done
    fi
    
    # Calcular progreso basado en archivos procesados
    progress_bar $TOTAL_OPS $copied_count
done

# Nueva línea después de la barra de progreso
echo ""

# Verificar que todos los archivos estén copiados
if [ $copied_count -lt $TOTAL_OPS ]; then
    rich_printer "[yellow]Advertencia: Solo se procesaron ${copied_count}/${TOTAL_OPS} archivos.[/yellow]"
    # Intentar copiar los archivos faltantes uno por uno
    missing_count=0
    for ((i=1; i<=ARRAY_LEN; i+=2)); do
        src="${COPY_OPS[i]}"
        dst="${COPY_OPS[i+1]}"
        if ! mp fs ls "$dst" >/dev/null 2>&1; then
            if mp fs cp "$src" "$dst" >/dev/null 2>&1; then
                missing_count=$((missing_count + 1))
                rich_printer "[dim]Copiado: $(basename "$src")[/dim]"
            fi
        fi
    done
    if [ $missing_count -gt 0 ]; then
        rich_printer "[green]✓ ${missing_count} archivos adicionales copiados.[/green]"
        copied_count=$((copied_count + missing_count))
    fi
fi

rich_printer "[green]✓ ${copied_count}/${TOTAL_OPS} archivos procesados.[/green]"

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
