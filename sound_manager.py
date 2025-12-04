# sound_manager.py
# Propósito: Ya esta terminado.

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

def _duty_off(b):
    if hasattr(b, 'duty_u16'):
        b.duty_u16(0)
    elif hasattr(b, 'duty'):
        b.duty(0)

def _duty_on(b):
    if hasattr(b, 'duty_u16'):
        b.duty_u16(32768)
    elif hasattr(b, 'duty'):
        b.duty(512)

def play_music_loop(buzzer):
    global current_song
    if not current_song:
        print("Error: No hay ninguna canción cargada en el sound_manager.")
        return

    piece = current_song.PIECE
    notes = current_song.NOTES
    
    note_index = 0
    total_notes = len(piece)

    while True:
        try:
            # Get the current note
            frequency, duration = piece[note_index]

            # Play the note
            if frequency == notes['SILENCE']:
                _duty_off(buzzer)
            else:
                buzzer.freq(frequency)
                _duty_on(buzzer)
            
            # Wait for the duration of the note
            time.sleep_ms(int(duration))

            # Move to the next note
            note_index = (note_index + 1) % total_notes

        except Exception as e:
            print(f"Error en el bucle de música: {e}")
            _duty_off(buzzer)
            # Reset index on error and wait before retrying
            note_index = 0
            time.sleep_ms(1000)
