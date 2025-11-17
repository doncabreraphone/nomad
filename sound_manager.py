from machine import PWM
import time

# --- Sound Manager ---
# Este módulo actúa como un reproductor de música genérico.

# Variable global para almacenar la canción actual
current_song = None

def load_song(song_module):
    """Carga una canción desde un módulo de música."""
    global current_song
    if hasattr(song_module, 'PIECE') and hasattr(song_module, 'NOTES'):
        current_song = song_module
        print(f"Canción cargada exitosamente.")
    else:
        print("Error: El módulo de la canción no tiene el formato correcto (falta PIECE o NOTES).")

def play_music_loop(buzzer):
    """Reproduce la canción cargada actualmente en un bucle infinito."""
    global current_song
    
    if not current_song:
        print("Error: No hay ninguna canción cargada en el sound_manager.")
        return

    print("Iniciando bucle de música de fondo...")
    
    piece = current_song.PIECE
    notes = current_song.NOTES

    while True:
        try:
            for frequency, duration in piece:
                # La frecuencia ya está resuelta en el módulo de la canción
                if frequency == notes['SILENCE']:
                    buzzer.duty_u16(0)
                else:
                    buzzer.freq(frequency)
                    buzzer.duty_u16(32768)  # 50% duty cycle
                
                time.sleep_ms(duration)
        except Exception as e:
            print(f"Error en el bucle de música: {e}")
            buzzer.duty_u16(0)
            time.sleep_ms(1000) # Espera un poco antes de reintentar