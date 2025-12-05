# main.py
# Propósito:  El director de orquesta. Inicializa el hardware, corre el bucle principal (while True), lee los inputs y llama al engine para actualizar el juego y al renderer para dibujar.

import time
import _thread
import hardware
import renderer
import sound_manager
import assets
import config

# Scenes
import intro_scene
import walk_scene
import hq_scene
import wifi_manager
import menus.main_menu as main_menu

# --- Configuración e Inicialización ---

print("Starting system...")

# 1. Inicializar Hardware
try:
    print("Initializing hardware...")
    # Obtenemos oled, buzzer y los botones A y B
    oled, buzzer, button_a, button_b = hardware.init_hardware()
    print("Hardware initialized successfully")
except Exception as e:
    print(f"ERROR initializing hardware: {e}")
    import sys
    sys.print_exception(e)
    # Intentar mostrar error en display si es posible
    try:
        from machine import Pin, I2C
        from ssd1306 import SSD1306_I2C
        import config
        i2c = I2C(0, scl=Pin(config.PIN_SCL), sda=Pin(config.PIN_SDA))
        oled = SSD1306_I2C(config.OLED_WIDTH, config.OLED_HEIGHT, i2c)
        oled.fill(0)
        oled.text("ERROR", 0, 0)
        oled.text("Hardware init", 0, 10)
        oled.text("failed", 0, 20)
        oled.show()
    except:
        pass
    raise

# 2. Inicializar Sonido
try:
    print("Loading song...")
    # Verificar que SONG_INTRO esté disponible
    if assets.SONG_INTRO is None:
        print("WARNING: SONG_INTRO is None, skipping music")
    else:
        # Cargamos la canción desde los assets
        # Nota: sound_manager.load_song espera un módulo con PIECE y NOTES
        sound_manager.load_song(assets.SONG_INTRO)
        # Iniciamos la música en un hilo separado para que suene durante la intro
        _thread.start_new_thread(sound_manager.play_music_loop, (buzzer,))
        print("Song loaded and music thread started")
except Exception as e:
    print(f"WARNING: Could not start music: {e}")
    import sys
    sys.print_exception(e)

def draw_menu(oled, selected_index):
    oled.fill(0)
    oled.text("MAIN MENU", 25, 0)
    
    options = ["1. Launch Game", "2. Uplink", "3. Manual"]
    
    for i, option in enumerate(options):
        y = 20 + (i * 12)
        prefix = "> " if i == selected_index else "  "
        oled.text(prefix + option, 0, y)
        
    oled.show()

def show_qr_code(oled):
    oled.fill(0)
    oled.text("MANUAL QR", 25, 0)
    # Placeholder box for QR
    oled.fill_rect(32, 15, 64, 48, 1)
    oled.fill_rect(34, 17, 60, 44, 0) # Inner empty
    oled.text("SCAN ME", 35, 35)
    oled.show()
    time.sleep(3)

# --- Bucle Principal ---

# 1. Play Intro Scene
try:
    print("Playing intro scene...")
    # Pasamos el botón para que espere la pulsación
    # Asegúrate de que 'intro_scene.py' esté actualizado en el dispositivo
    intro_scene.play_sequence(oled, button_a)
    print("Intro scene completed")
except Exception as e:
    print(f"ERROR playing intro: {e}")
    import sys
    sys.print_exception(e)
    # Mostrar error en display
    try:
        oled.fill(0)
        oled.text("ERROR", 0, 0)
        oled.text("Intro failed", 0, 10)
        oled.show()
        time.sleep(3)
    except:
        pass
    # Si falla la intro, esperamos un poco para que se pueda leer el error
    time.sleep(2)

# 2. Menu Loop
try:
    print("Initializing main menu...")
    menu = main_menu.MainMenu(oled)
    print("Main menu initialized")
except Exception as e:
    print(f"ERROR initializing menu: {e}")
    import sys
    sys.print_exception(e)
    # Mostrar error en display
    try:
        oled.fill(0)
        oled.text("ERROR", 0, 0)
        oled.text("Menu init", 0, 10)
        oled.text("failed", 0, 20)
        oled.show()
        time.sleep(3)
    except:
        pass
    raise

print("Entering main loop...")
while True:
    try:
        # Ejecutar menú y esperar selección
        # El método run() maneja el bucle de dibujo y input internamente
        # Pasamos button_a para navegación (up/down) y button_b para selección (enter)
        selected_action = menu.run(button_a, button_b)
        
        print(f"Action selected: {selected_action}")
        
        if selected_action == "launch":
            print("Launching Game...")
            try:
                hq_scene.play_scene(oled)
                walk_scene.play_scene(oled)
            except Exception as e:
                print(f"ERROR in game scenes: {e}")
                import sys
                sys.print_exception(e)
        
        elif selected_action == "uplink":
            print("Starting Uplink...")
            try:
                wifi_manager.play_scene(oled)
            except Exception as e:
                print(f"ERROR in uplink scene: {e}")
                import sys
                sys.print_exception(e)
        
        elif selected_action == "manual":
            print("Showing Manual...")
            # Definir show_qr_code o moverlo a un módulo
            # show_qr_code(oled) # Asumiendo que existe localmente o mover a modulo
            pass # Placeholder
        
        elif selected_action == "contact":
            print("Contact info...")
            oled.fill(0)
            oled.text("CONTACT", 20, 20)
            oled.show()
            time.sleep(2)
    except Exception as e:
        print(f"ERROR in main loop: {e}")
        import sys
        sys.print_exception(e)
        # Intentar mostrar error en display
        try:
            oled.fill(0)
            oled.text("ERROR", 0, 0)
            oled.text("Main loop", 0, 10)
            oled.text("error", 0, 20)
            oled.show()
            time.sleep(2)
        except:
            pass
        
    # Al volver, el bucle while True reinicia el menú
