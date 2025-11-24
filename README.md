# CODENAME NOMAD — Firmware ESP32 (MicroPython)

Firmware del dispositivo NOMAD. Entorno: ESP32 + MicroPython.  
Objetivo: desarrollo rápido, simulación en Wokwi y carga automática.

---

## Configuración rápida

### 1. Requisitos
Instala `mpremote`:
```bash
pip3 install mpremote
```

### 2. Entorno virtual
```bash
python3 -m venv .venv
source .venv/bin/activate    # macOS/Linux
# .venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### 3. Simulador Wokwi en VS Code
1. Abrí la paleta de comandos (`Cmd+Shift+P` / `Ctrl+Shift+P`).
2. Seleccioná: **Wokwi: Start Simulator**.
3. Dejá la pestaña abierta.

### 4. Cargar firmware (simulador o hardware)
Con el entorno virtual activo:
```bash
./scripts/update_device.sh
```

En hardware físico:
```bash
./scripts/update_device.sh /dev/cu.usbmodemXXXX
```

---

## Scripts útiles

### Generar animaciones
Convierte frames `.c` a un archivo de animación para MicroPython.

Uso:
```bash
python3 scripts/generate_animation.py <nombre_animacion>_animation.py
```

Ejemplo:
```bash
python3 scripts/generate_animation.py travel_animation.py
```

Resultado: `travel_animation.py` con `TRAVEL_ANIMATION`.



---

## Estructura mínima del proyecto

```
/
 main.py
 assets/
 scripts/
   generate_animation.py
   update_device.sh
 requirements.txt
```
