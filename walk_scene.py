# walk_scene.py
# Propósito: Muestra la animación de caminata (la escena original).

import time
import renderer
import config

def play_scene(oled):
    """
    Ejecuta la escena de caminata.
    Retorna cuando el usuario sale (o infinito si no hay salida definida aún).
    """
    # Inicializar Renderer localmente o recibirlo
    view = renderer.Renderer(oled)
    
    print("Starting walk scene...")
    
    frame_actual = 0
    keep_playing = True
    
    # TODO: Definir condición de salida (ej. botón)
    # Por ahora corre indefinidamente hasta reset o interrupción externa
    # Si queremos que sea interrumpible, necesitamos pasarle un input_handler
    
    while keep_playing:
        # 1. Dibujar (Renderer)
        view.draw_walk_frame(frame_actual)
        
        # 2. Control de Tiempos
        frame_actual += 1
        time.sleep_ms(config.ANIMATION_SPEED_MS)
        
        # TODO: Check input to exit?
