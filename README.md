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
https://javl.github.io/image2cpp/
Las imagenes hay que ponerlas de a una, ordenadas o sale mal.

Este script ahora es interactivo. Simplemente ejecutalo y seguí las instrucciones:

Uso:
```bash
python3 scripts/generate_animation.py
```

El script te mostrará un menú para que elijas la animación a generar y te preguntará si deseas invertir los colores.



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


# MUSIC
https://basicpitch.spotify.com/

https://arduinomidi.netlify.app/

https://aisonggenerator.io/es/midi-editor

https://suno.com/


# ART
https://voidless.dev/image-gen