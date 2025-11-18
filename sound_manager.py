from machine import PWM
import time

current_song = None

def load_song(song_module):
    global current_song
    if hasattr(song_module, 'PIECE') and hasattr(song_module, 'NOTES'):
        current_song = song_module
        print("Canción cargada exitosamente.")
    else:
        print("Error: El módulo de la canción no tiene el formato correcto (falta PIECE o NOTES).")

def play_music_loop(buzzer):
    global current_song
    if not current_song:
        print("Error: No hay ninguna canción cargada en el sound_manager.")
        return

    piece = current_song.PIECE
    notes = current_song.NOTES

    while True:
        try:
            for frequency, duration in piece:
                if frequency == notes['SILENCE']:
                    buzzer.duty_u16(0)
                else:
                    buzzer.freq(frequency)
                    buzzer.duty_u16(32768)
                time.sleep_ms(int(duration))
        except Exception as e:
            print(f"Error en el bucle de música: {e}")
            buzzer.duty_u16(0)
            time.sleep_ms(1000)