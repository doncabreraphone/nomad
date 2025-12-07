# menus/main_menu.py
# Propósito: Menú principal estilo Flipper Zero con scroll, iconos y navegación avanzada.

import time
import math
import framebuf
import assets
import config
import fonts

class MainMenu:
    # Constantes de tiempo para botones (ms)
    LONG_PRESS_MS = 400
    DOUBLE_CLICK_MS = 350

    def __init__(self, oled):
        self.oled = oled
        
        # Opciones del menú
        # (Label, Callback ID)
        self.options = [
            ("Launch", "launch"),
            ("Uplink", "uplink"),
            ("Manual", "manual"),
            ("Contact", "contact")
        ]
        
        self.selected_index = 0
        self.scroll_offset = 0 # Desplazamiento vertical (en píxeles o índice, veremos)
        
        # Configuración visual
        self.item_height = 18 # Altura de cada item
        self.visible_items = 3 # Siempre mostrar 3 items visibles
        self.menu_x = 2  # Posición X del menú (a la izquierda)
        self.menu_width = 120  # Ancho del menú (128 - 2 - 6 para scroll bar a la derecha)
        
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
        
        # Calcular posición inicial para mostrar siempre 3 items visibles
        # Total altura para 3 items: 3 * 18 = 54px
        # Pantalla tiene 64px, espacio disponible: 64 - 54 = 10px
        # Padding superior: 10 / 2 = 5px
        start_y = 5
        
        # Calcular qué items mostrar basándose en el índice seleccionado
        # Siempre mostrar 3 items: intentar centrar el seleccionado si es posible
        if len(self.options) <= self.visible_items:
            # Si hay 3 o menos items, mostrar todos desde el inicio
            display_start = 0
        else:
            # Si hay más de 3 items, centrar el seleccionado cuando sea posible
            # El seleccionado debería estar en la posición media (índice 1 de los 3 visibles)
            display_start = max(0, self.selected_index - 1)
            # Asegurar que no se salga del rango
            display_start = min(display_start, len(self.options) - self.visible_items)
        
        # Dibujar los 3 items visibles
        for display_idx in range(self.visible_items):
            item_idx = display_start + display_idx
            
            # Si no hay más items, no dibujar
            if item_idx >= len(self.options):
                break
            
            label, _ = self.options[item_idx]
            y = start_y + (display_idx * self.item_height)
            
            # Si es el seleccionado
            if item_idx == self.selected_index:
                self._fill_round_rect(self.menu_x, y, self.menu_width, self.item_height, 4, 1)
                text_y = y + 2  # Alineación vertical
                text_x = self.menu_x + 20  # Espacio para el icono
                fonts.draw(self.oled, label, text_x, text_y, font_data=fonts.FONT_BOLD, color=0)
                self.oled.blit(self.icon_fb, self.menu_x + 4, y + 2, 1)
                
            else:
                # No seleccionado - usar FONT_REGULAR para consistencia visual
                text_y = y + 2  # Misma alineación vertical que el seleccionado
                text_x = self.menu_x + 20  # Mismo offset que el seleccionado
                fonts.draw(self.oled, label, text_x, text_y, font_data=fonts.FONT_REGULAR, color=1)
        
        # Scroll Bar (Derecha) - patrón de píxeles alternados
        bar_height = max(4, 64 // len(self.options))
        bar_y = int((self.selected_index / max(1, len(self.options) - 1)) * (64 - bar_height))
        
        # Scroll bar a la derecha
        scroll_bar_x = 126  # Posición X a la derecha (128 - 2)
        
        # Dibujar pista con patrón de píxeles alternados (on/off)
        # Patrón: un píxel on, un píxel off
        for y_pos in range(0, 64):
            if y_pos % 2 == 0:  # Píxeles pares: on
                self.oled.pixel(scroll_bar_x, y_pos, 1)
            # Píxeles impares: off (ya está en 0 por el fill(0))
        
        # Dibujar barra (handle) centrada horizontalmente en la pista
        # La barra es un rectángulo sólido de 3px de ancho centrado
        bar_width = 3
        bar_x = scroll_bar_x - (bar_width // 2)  # Centrar la barra en la pista
        self.oled.fill_rect(bar_x, bar_y, bar_width, bar_height, 1)
        
        self.oled.show()

    def run(self, button_up_down, button_select):
        """
        Bucle principal del menú
        button_up_down (A): Click = Bajar, Long Press = Subir
        button_select (B): Click = Aceptar
        """
        last_selected_index = -1
        needs_redraw = True
        
        while True:
            # Solo redibujar si hay cambios o es la primera vez
            if needs_redraw or self.selected_index != last_selected_index:
                self.draw()
                last_selected_index = self.selected_index
                needs_redraw = False
            
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
                    needs_redraw = True
                    
                    # Esperar a que suelte
                    while button_up_down.value() == 0:
                        time.sleep_ms(50)
                else:
                    # Acción: Bajar (Siguiente)
                    print("Button A Short: DOWN")
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                    needs_redraw = True
            
            # --- Botón B (Selección) ---
            if button_select.value() == 0: # Presionado
                print("Button B: SELECT")
                # Debounce simple
                while button_select.value() == 0:
                    time.sleep_ms(50)
                return self.options[self.selected_index][1]
            
            # Aumentar el sleep para dar más tiempo al hilo de música
            time.sleep_ms(50)
