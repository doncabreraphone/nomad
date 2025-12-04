# menus/main_menu.py
# Propósito: Menú principal estilo Flipper Zero con scroll, iconos y navegación avanzada.

import time
import math
import framebuf
import assets
import config

class MainMenu:
    # Constantes de tiempo para botones (ms)
    LONG_PRESS_MS = 400
    DOUBLE_CLICK_MS = 350

    def __init__(self, oled):
        self.oled = oled
        
        # Opciones del menú
        # (Label, Callback ID)
        self.options = [
            ("Launch Game", "launch"),
            ("Uplink", "uplink"),
            ("Manual", "manual"),
            ("Contact", "contact")
        ]
        
        self.selected_index = 0
        self.scroll_offset = 0 # Desplazamiento vertical (en píxeles o índice, veremos)
        
        # Configuración visual
        self.item_height = 18 # Altura de cada item
        self.visible_items = 3 # Cuántos items caben en pantalla (64px / 18 = 3.5)
        
        # Icono CPU (16x16)
        # Usamos el icono original (Blanco sobre Transparente)
        # Si queremos "invertirlo" (Negro sobre Blanco), simplemente usamos la versión NO invertida
        # al hacer blit sobre el fondo blanco, si el asset original es "negativo".
        
        # Pero como probamos invertir bits y salió mal, volvemos a cargar el asset ORIGINAL
        # y vamos a probar dibujarlo directamente.
        self.icon_fb = framebuf.FrameBuffer(assets.CPU_ICON, 16, 16, framebuf.MONO_HLSB)

    def _fill_round_rect(self, x, y, w, h, r, col):
        # Hand-tuned for r=4 look to be smoother on 128x64
        if r == 4:
            self.oled.fill_rect(x + 2, y, w - 4, 1, col)
            self.oled.fill_rect(x + 1, y + 1, w - 2, 1, col)
            self.oled.fill_rect(x, y + 2, w, h - 4, col)
            self.oled.fill_rect(x + 1, y + h - 2, w - 2, 1, col)
            self.oled.fill_rect(x + 2, y + h - 1, w - 4, 1, col)
            return

        # Fallback for other radii
        if r <= 0:
            self.oled.fill_rect(x, y, w, h, col)
            return
        for dy in range(r):
            dx = int(math.floor(math.sqrt(r * r - dy * dy)))
            left = x + r - dx
            right = x + w - r + dx
            self.oled.fill_rect(left, y + dy, right - left, 1, col)
            self.oled.fill_rect(left, y + h - 1 - dy, right - left, 1, col)
        self.oled.fill_rect(x, y + r, w, h - 2 * r, col)

    def draw(self):
        self.oled.fill(0)
        
        # Calcular ventana de visualización
        selection_y = 22 # (64 - 18) / 2 = 23 aprox
        
        for i, (label, _) in enumerate(self.options):
            # Distancia relativa al seleccionado
            relative_idx = i - self.selected_index
            
            # Posición Y base
            y = selection_y + (relative_idx * self.item_height)
            
            # Si está muy lejos de la pantalla, no dibujamos
            if y < -self.item_height or y > 64:
                continue
                
            # Si es el seleccionado
            if i == self.selected_index:
                self._fill_round_rect(2, y, 118, self.item_height, 4, 1)
                self.oled.text(label, 24, y + 5, 0)
                self.oled.blit(self.icon_fb, 6, y + 1, 1)
                
            else:
                # No seleccionado
                # Texto blanco sobre fondo negro
                self.oled.text(label, 24, y + 5, 1)
                
                # Sin icono
        
        # Scroll Bar (Derecha)
        for i in range(0, 64, 4):
            self.oled.pixel(126, i, 1)
            
        bar_height = max(4, 64 // len(self.options))
        bar_y = int((self.selected_index / (len(self.options) - 1)) * (64 - bar_height))
        self.oled.fill_rect(125, bar_y, 3, bar_height, 1)
        
        self.oled.show()

    def run(self, button_up_down, button_select):
        """
        Bucle principal del menú
        button_up_down (A): Click = Bajar, Long Press = Subir
        button_select (B): Click = Aceptar
        """
        last_interaction = time.ticks_ms()
        
        while True:
            self.draw()
            
            # --- Botón A (Navegación) ---
            if button_up_down.value() == 0: # Presionado
                press_start = time.ticks_ms()
                
                # Esperar a que suelte o supere umbral de "largo"
                long_press = False
                while button_up_down.value() == 0:
                    if time.ticks_diff(time.ticks_ms(), press_start) > self.LONG_PRESS_MS:
                        long_press = True
                        break
                    time.sleep_ms(10)
                
                if long_press:
                    # Acción: Subir (Anterior)
                    print("Button A Long: UP")
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                    
                    # Esperar a que suelte
                    while button_up_down.value() == 0:
                        time.sleep_ms(50)
                else:
                    # Acción: Bajar (Siguiente)
                    print("Button A Short: DOWN")
                    self.selected_index = (self.selected_index + 1) % len(self.options)
            
            # --- Botón B (Selección) ---
            if button_select.value() == 0: # Presionado
                print("Button B: SELECT")
                # Debounce simple
                while button_select.value() == 0:
                    time.sleep_ms(50)
                return self.options[self.selected_index][1]
            
            time.sleep_ms(20)
