# renderer.py
# Propósito: La "Vista". Sabe cómo dibujar las pantallas. Tiene funciones como draw_hq_screen(), draw_log_entry(), draw_combat_anim(). Combina los sprites con el texto.

import framebuf
import assets

class Renderer:
    def __init__(self, oled):
        self.oled = oled
        self.anim_fb = []
        self._load_assets()
        
    def _load_assets(self):
        # Convertimos cada bytearray de nuestros assets en un objeto de imagen
        for frame_data in assets.WALK_ANIMATION:
            fb = framebuf.FrameBuffer(frame_data, 128, 64, framebuf.MONO_HLSB)
            self.anim_fb.append(fb)
            
    def draw_walk_frame(self, frame_index):
        # Aseguramos que el índice esté dentro del rango
        idx = frame_index % len(self.anim_fb)
        frame_a_dibujar = self.anim_fb[idx]
        
        self.oled.fill(0)
        self.oled.blit(frame_a_dibujar, 0, 0)
        self.oled.show()
        
    def get_frame_count(self):
        return len(self.anim_fb)
