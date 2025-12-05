# intro_scene.py

import time
import framebuf
import assets # Asumimos que tus bytearrays están acá

def play_sequence(oled, button=None):
    """
    Ejecuta la secuencia de inicio cinematográfica:
    Fade in de Cypher + Vuelo de Nomad/Protocol.
    Bloquea la ejecución hasta terminar.
    """
    
    # ... (Rest of setup) ...
    # 1. Setup de Buffers (Dimensiones REALES de assets)
    # Es vital que 'assets.LOGO_CYPHER', etc., existan en tu archivo assets.py
    # Cypher Logo: 128x64
    fb_cypher = framebuf.FrameBuffer(assets.LOGO_CYPHER, 128, 64, framebuf.MONO_HLSB)
    # Nomad Logo: 46x13
    fb_nomad = framebuf.FrameBuffer(assets.LOGO_NOMAD, 46, 13, framebuf.MONO_HLSB)
    # Protocol Logo: 61x13
    fb_proto = framebuf.FrameBuffer(assets.LOGO_PROTOCOL, 61, 13, framebuf.MONO_HLSB)

    # --- FASE 1: FADE IN (CONTRASTE) ---
    oled.contrast(0) # Empezar "apagado"
    oled.fill(0)
    # Dibujamos el logo principal centrado verticalmente si es necesario, o 0,0 si ocupa todo
    oled.blit(fb_cypher, 0, 0) 
    oled.show()
    
    # Subir brillo gradualmente (optimizado: menos pasos, más rápido)
    for i in range(0, 256, 16):  # Incrementos más grandes
        oled.contrast(i)
        time.sleep_ms(15)  # Menos tiempo entre pasos
    
    # Pausa dramática de 3 segundos para leer CYPHER
    # (Aquí sonaría el blues de fondo si se inició antes en main.py)
    time.sleep(3) 

    # --- FASE 2: ANIMACIÓN DE TEXTO (FLY-IN) ---
    # Optimizado para mejor rendimiento
    target_y = 26   # Altura centrada verticalmente sobre el logo
    
    # Posiciones finales calculadas
    stop_nomad_x = 10  # Un poquito más a la derecha para balancear visualmente
    stop_proto_x = 60  # 10 + 46 + 4
    
    left_x = -60    # Nomad entra desde izq (afuera)
    right_x = 128   # Protocol entra desde der (afuera)
    
    step = 6 # Velocidad de movimiento (aumentada para menos frames)
    frame_skip = 0  # Contador para saltar frames de actualización
    last_nomad_x = -1000  # Para tracking de cambios
    last_proto_x = 2000

    while left_x < stop_nomad_x or right_x > stop_proto_x:
        # Calcular próximo paso primero
        if left_x < stop_nomad_x: 
            left_x += step
            if left_x > stop_nomad_x: left_x = stop_nomad_x
            
        if right_x > stop_proto_x: 
            right_x -= step
            if right_x < stop_proto_x: right_x = stop_proto_x
        
        # Solo actualizar display cada 2 frames para mejor rendimiento
        frame_skip = (frame_skip + 1) % 2
        if frame_skip == 0 or left_x >= stop_nomad_x and right_x <= stop_proto_x:
            # Calcular área mínima que necesita actualización
            min_x = min(int(left_x), int(right_x), 0)
            max_x = max(int(left_x) + 46, int(right_x) + 61, 128)
            width = max_x - min_x
            
            # Limpiar solo el área que necesita actualización (más eficiente)
            oled.fill_rect(max(0, min_x), target_y, min(128, width), 14, 0)
            
            # Dibujar en nuevas posiciones
            oled.blit(fb_nomad, int(left_x), target_y)
            oled.blit(fb_proto, int(right_x), target_y)
            
            # Update físico (solo cuando hay cambios significativos)
            oled.show()
        
        time.sleep_ms(8) # Control de FPS (reducido ligeramente)
    
    # Asegurar dibujo final en posiciones exactas
    oled.fill_rect(0, target_y, 128, 14, 0)
    oled.blit(fb_nomad, stop_nomad_x, target_y)
    oled.blit(fb_proto, stop_proto_x, target_y)
    oled.show()

    # --- FASE 3: INPUT WAIT ---
    # Pequeño delay para apreciar el logo completo
    time.sleep_ms(500)
    
    # Mostramos PRESS TO START debajo de CYPHER (que termina en y=64)
    # Pero la pantalla tiene 64px de alto.
    # El texto NOMAD PROTOCOL está centrado en y=26, alto 13 -> va de 26 a 39.
    # Queda espacio abajo: de 39 a 64 hay 25 px.
    # Podemos poner PRESS TO START en y=55 (bottom) sin borrar los logos.
    
    prompt_y = 55
    
    print("Waiting for button press...")
    if button:
        # Debounce
        time.sleep_ms(200)
        
        blink_state = False
        last_blink = time.ticks_ms()
        
        while True:
            # Lógica de parpadeo del texto "PRESS TO START"
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, last_blink) > 800: # Parpadeo lento
                blink_state = not blink_state
                last_blink = current_time
                
                # Limpiar SOLO el área del texto prompt (abajo), no tocar logos
                oled.fill_rect(0, prompt_y, 128, 8, 0)
                
                if blink_state:
                    # Mostrar PRESS TO START
                    # Centrado: "PRESS TO START" son ~14 chars * 8px = 112px
                    # (128 - 112) / 2 = 8
                    oled.text("PRESS TO START", 8, prompt_y) 
                
                oled.show()

            # Check botón
            val = button.value()
            if val == 0:
                print("Button pressed!")
                break
            
            time.sleep_ms(50)

        # Feedback visual final
        oled.invert(True)
        time.sleep_ms(100)
        oled.invert(False)
        
        # Esperar a que suelte
        while button.value() == 0:
            time.sleep_ms(50)
            
    else:
        time.sleep(2)