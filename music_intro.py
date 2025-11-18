# music_intro.py
# Contiene los datos de la melodía "Alley Cat Jazz"

# --- DICCIONARIO DE NOTAS (Frecuencias en Hz) ---
NOTES = {
    'SILENCE': 0,
    'G#3': 208,
    'B3': 247,
    'C#4': 277,
    'D#4': 311,
    'E4': 330,
    'F#4': 370,
}

# --- LA COMPOSICIÓN: EL SOLO DE JAZZ ---
TEMPO = 100
PIECE = [
    (NOTES['G#3'], TEMPO), (NOTES['SILENCE'], TEMPO),
    (NOTES['B3'], TEMPO), (NOTES['SILENCE'], TEMPO),
    (NOTES['C#4'], TEMPO), (NOTES['SILENCE'], TEMPO),
    (NOTES['F#4'], TEMPO * 2),
    (NOTES['F#4'], TEMPO),
    (NOTES['E4'], TEMPO),
    (NOTES['SILENCE'], TEMPO * 2),
    (NOTES['G#3'], TEMPO),
    (NOTES['SILENCE'], TEMPO),
    (NOTES['D#4'], TEMPO * 2),
    (NOTES['D#4'], TEMPO),
    (NOTES['C#4'], TEMPO),
    (NOTES['SILENCE'], TEMPO * 2),
    (NOTES['G#3'], TEMPO),
    (NOTES['SILENCE'], TEMPO),
    (NOTES['B3'], TEMPO),
    (NOTES['SILENCE'], TEMPO),
    (NOTES['B3'], TEMPO),
    (NOTES['C#4'], TEMPO),
    (NOTES['SILENCE'], TEMPO * 2),
    (NOTES['G#3'], TEMPO),
    (NOTES['SILENCE'], TEMPO),
    (NOTES['D#4'], TEMPO),
    (NOTES['E4'], TEMPO),
    (NOTES['D#4'], TEMPO),
    (NOTES['B3'], TEMPO),
    (NOTES['C#4'], TEMPO),
    (NOTES['G#3'], TEMPO),
    (NOTES['B3'], TEMPO),
    (NOTES['C#4'], TEMPO),
    (NOTES['F#4'], TEMPO * 2),
    (NOTES['F#4'], TEMPO),
    (NOTES['E4'], TEMPO),
    (NOTES['SILENCE'], TEMPO * 2),
    (NOTES['G#3'], TEMPO),
    (NOTES['SILENCE'], TEMPO),
    (NOTES['D#4'], TEMPO * 2),
    (NOTES['D#4'], TEMPO),
    (NOTES['C#4'], TEMPO),
    (NOTES['SILENCE'], TEMPO * 2),
    (NOTES['G#3'], TEMPO),
    (NOTES['G#3'], TEMPO),
    (NOTES['G#3'], TEMPO)
]