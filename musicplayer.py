import os
import sys
import time
import pygame
import readchar
import textwrap
import opacidad_temporal as opacidad
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, ProgressColumn, BarColumn, TaskProgressColumn, TextColumn
__import__('pkg_resources').declare_namespace(__name__)

#variables globaes
# Constantes NO MODIFICAR.
MUSIC_PLAYER_NAME = "GingaPlayer (銀河プレーヤー)"
AUTOR = "LDTech"

VISIBLE_ITEMS = 10
TABLE_COLOR_STYLE = "red"
NORMAL_ITEM_COLOR = "bright_green"
SELECTED_ITEM_COLOR = "bright_cyan"
# Configuración inicial
if os.name == 'nt':
    import msvcrt

# Guardar configuracion original
#opacidad.backup_file()

# Detectar entorno y aplicar configuración de opacidad
opacidad.detect_environment()
json_file_path = os.path.join(os.environ["LOCALAPPDATA"], 
                              "Packages", 
                              "Microsoft.WindowsTerminal_8wekyb3d8bbwe", 
                              "LocalState", 
                              "settings.json")
environment = opacidad.detect_environment()
if environment == "CMD":
    opacidad.modify_cmd_registry()
elif environment == "PowerShell":
    opacidad.modify_powershell_profile()
else:
    opacidad.modify_windows_terminal(json_file_path)


console = Console()
default_music_folder = os.path.join(os.environ['USERPROFILE'], "Music") if os.name == "nt" else os.path.expanduser("~/Music")
max_visible_items = VISIBLE_ITEMS

# ========================
# Clases personalizadas
# ========================
class TimeElapsedTotalColumn(ProgressColumn):
    """Columna personalizada para mostrar tiempo transcurrido/total"""
    def __init__(self, total_duration: float):
        super().__init__()
        self.total_duration = total_duration
        self.total_time_str = time.strftime("%H:%M:%S", time.gmtime(total_duration))

    def render(self, task) -> Text:
        elapsed = task.completed
        elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
        return Text(f"[{elapsed_str}/{self.total_time_str}]", style="bright_cyan")


# ========================
# Listar Directorios.
# ========================

def get_directory_contents(current_folder):
    items = []
    parent_dir = os.path.dirname(current_folder)
    
    # Añadir '..' si no estamos en el directorio raíz
    if parent_dir != current_folder:
        items.append(("..", True))  # (nombre, es_directorio)
    
    dirs = []
    files = []
    try:
        for item in os.listdir(current_folder):
            item_path = os.path.join(current_folder, item)
            if os.path.isdir(item_path) and item not in (".", ".."):
                dirs.append(item)
            elif os.path.isfile(item_path) and item.lower().endswith((".mp3", ".wav")):
                files.append(item)
    except PermissionError:
        pass
    
    # Ordenar alfabéticamente
    dirs.sort()
    files.sort()
    
    # Añadir directorios y archivos ordenados
    for d in dirs:
        items.append((d, True))
    for f in files:
        items.append((f, False))
    
    return items

# ========================
# Funciones de música
# ========================
def get_music_files(music_folder):
    return [f for f in os.listdir(music_folder) if f.endswith((".mp3", ".wav"))]

def play_music(file_path):
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()

def stop_music():
    pygame.mixer.music.stop()

def pause_music():
    pygame.mixer.music.pause()

def unpause_music():
    pygame.mixer.music.unpause()

def get_music_length(file_path):
    pygame.mixer.init()
    return pygame.mixer.Sound(file_path).get_length()

def set_volume(change):
    current_volume = pygame.mixer.music.get_volume()
    new_volume = max(0.0, min(1.0, current_volume + change))
    pygame.mixer.music.set_volume(new_volume)
    console.print(f"[bold yellow]Volumen: {int(new_volume * 100)}%[/bold yellow]", end="\r")

# ========================
# Interfaz de usuario
# ========================

def render_interface(items, selected_index, scroll_offset):
    table = Table(border_style=TABLE_COLOR_STYLE)
    table.add_column("#", justify="right", style="dim")
    table.add_column("Elemento", width=50)
    
    for i in range(scroll_offset, min(len(items), scroll_offset + max_visible_items)):
        item_name, is_dir = items[i]
        if i == selected_index:
            style = SELECTED_ITEM_COLOR
        else:
            style = "bold blue" if is_dir else NORMAL_ITEM_COLOR
        icon = "📁" if is_dir else "🎵"
        wrapped_name = textwrap.shorten(f"{icon} {item_name}", width=45, placeholder="...")
        table.add_row(str(i + 1), Text(wrapped_name, style=style))
    
    return table

#  OLD CODE 

#def render_interface(songs, selected_index, scroll_offset):
#    table = Table(border_style=TABLE_COLOR_STYLE)
#    table.add_column("#", justify="right", style="dim")
#    table.add_column("Canción")
    
#    for i in range(scroll_offset, min(len(songs), scroll_offset + max_visible_items)):
#        style = SELECTED_ITEM_COLOR if i == selected_index else NORMAL_ITEM_COLOR
#        table.add_row(str(i + 1), Text(songs[i], style=style))
    
#    return table

def handle_arrow_keys(key):
    """Maneja teclas de flecha y teclas alternativas (W y S)."""
    if key in ('\x1b[A', 'w'):  # Flecha arriba o 'W'
        return 'up'
    elif key in ('\x1b[B', 's'):  # Flecha abajo o 'S'
        return 'down'
    return key.lower()


def get_non_blocking_key():
    try:
        if os.name == 'nt':
            return msvcrt.getch().decode() if msvcrt.kbhit() else None
        else:
            import select
            return sys.stdin.read(1) if select.select([sys.stdin], [], [], 0)[0] else None
    except:
        return None

# ========================
# Menú de reproducción
# ========================
def playback_menu(song_path):
    song_name = os.path.basename(song_path)
    duration = get_music_length(song_path)
    start_time = time.time()

    # Ajuste dinámico del nombre
    try:
        terminal_width = os.get_terminal_size().columns - 45
    except OSError:
        terminal_width = 50

    wrapper = textwrap.TextWrapper(
        width=terminal_width,
        break_long_words=False,
        replace_whitespace=False,
        drop_whitespace=False
    )
    wrapped_name = wrapper.fill(song_name)

    # Configuración de la barra de progreso
    with Progress(
        TextColumn(f"[bold bright_green]Reproduciendo: {wrapped_name}"),
        BarColumn(bar_width=None),
        TaskProgressColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedTotalColumn(duration),
        console=console,
        refresh_per_second=15,
        expand=True
    ) as progress:
        
        task = progress.add_task("", total=duration)
        
        while pygame.mixer.music.get_busy():
            elapsed_time = time.time() - start_time
            progress.update(task, completed=elapsed_time)
            
            # Manejo de controles
            key = get_non_blocking_key()
            if key:
                key = handle_arrow_keys(key)
                if key == ' ':
                    toggle_play_pause()
                elif key in ('s', '\x1b'):
                    stop_music()
                    return
                elif key in ('+', '='):
                    set_volume(0.1)
                elif key == '-':
                    set_volume(-0.1)
            
            time.sleep(0.05)

# ========================
# Función principal
# ========================
# def music_player(music_folder):
#     # Initialize Pygame
#     pygame.init()
    
#     # Get the list of music files from the specified folder
#     songs = get_music_files(music_folder)
    
#     # Check if there are no music files found
#     if not songs:
#         console.print("[bold red]No se encontraron archivos de música.[/bold red]")
#         return
    
#     # Initialize the selected index and scroll offset
#     selected_index = 0
#     scroll_offset = 0
    
#     # Start the main loop of the music player
#     while True:
#         # Clear the console and print the header information
#         console.clear()
#         console.print(f"[bold bright_white]Made by {AUTOR}[/bold bright_white]", justify="left")
#         console.print(f"🎵 [bold bright_cyan]{MUSIC_PLAYER_NAME}[/bold bright_cyan] 🎵", justify="center")
#         console.print("Controles:", "↑/W: Arriba", "↓/S: Abajo", "Enter: Reproducir", "+/-: Volumen", "ESC: Salir", sep=" | ")
#         console.print(render_interface(songs, selected_index, scroll_offset))
        
#         try:
#             # Read the user's key input
#             key = readchar.readkey()
#             key = handle_arrow_keys(key)
#         except KeyboardInterrupt:
#             # Break the loop if there's a KeyboardInterrupt
#             break
        
#         # Handle key inputs for navigating the list and controlling the music player
#         if key in ('w', 'up') and selected_index > 0:
#             selected_index -= 1
#             if selected_index < scroll_offset:
#                 scroll_offset = selected_index
#         elif key in ('s', 'down') and selected_index < len(songs) - 1:
#             selected_index += 1
#             if selected_index >= scroll_offset + max_visible_items:
#                 scroll_offset += 1
#         elif key == '\r':
#             # Play the selected song and open the playback menu
#             song_path = os.path.join(music_folder, songs[selected_index])
#             play_music(song_path)
#             playback_menu(song_path)
#         elif key in ('+', '='):
#             # Increase the volume
#             set_volume(0.1)
#         elif key == '-':
#             # Decrease the volume
#             set_volume(-0.1)
#         elif key in ('\x1b', 'q'):
#             # Exit the music player
#             opacidad.restore_configurations()
#             stop_music()
#             break

def music_player(start_folder):
    pygame.init()
    current_folder = start_folder
    selected_index = 0
    scroll_offset = 0
    current_song_path = None
    total_duration = 0
    start_time = 0
    paused = False
    paused_position = 0
    autoreproduccion = True
    saved_music_files = []
    current_music_index = -1
    
    while True:
        items = get_directory_contents(current_folder)
        
        console.clear()
        console.print(f"[bold bright_white]Made by {AUTOR}[/bold bright_white]", justify="left")
        console.print(f"📂 [bold yellow]{current_folder}[/bold yellow]")
        console.print(f"🎵 [bold bright_cyan]{MUSIC_PLAYER_NAME}[/bold bright_cyan] 🎵", justify="center")
        console.print("Controles:", 
                    "↑/W: Arriba", 
                    "↓/S: Abajo", 
                    "←/A: -5s", 
                    "→/D: +5s", 
                    "[Z] Detener", 
                    "[SPACE] Pausa", 
                    "[+/-] Volumen",
                    "[M] Modo AutoPlay", 
                    "ESC: Salir", sep=" | ")
        console.print(render_interface(items, selected_index, scroll_offset))

        console.print(f"\n[bold]Modo Autoplay:[/bold] {'✅ ON' if autoreproduccion else '❌ OFF'}")

        if current_song_path:
            song_name = os.path.basename(current_song_path)
            status = "[yellow]PAUSADO[/yellow]" if paused else "[green]REPRODUCIENDO[/green]"
            elapsed = time.time() - start_time if not paused else paused_position
            elapsed_str = time.strftime("%M:%S", time.gmtime(elapsed))
            total_str = time.strftime("%M:%S", time.gmtime(total_duration))
            
            progress_width = 50
            filled = int((elapsed / total_duration) * progress_width) if total_duration > 0 else 0
            bar = f"[{'=' * filled}{' ' * (progress_width - filled)}]"
            
            console.print(f"\n{status} {song_name}")
            console.print(f"[cyan]{elapsed_str} / {total_str}[/cyan]")
            console.print(f"[bright_green]{bar}[/bright_green]")
            console.print("Controles: [SPACE] Pausa/Reanuda  [Z] Detener  [+/-] Volumen")

        try:
            key = readchar.readkey().lower()
        except KeyboardInterrupt:
            break

        # Manejo de teclas
        if key == 'm':
            autoreproduccion = not autoreproduccion
            console.print(f"\n[bold yellow]Modo Autoplay {'activado' if autoreproduccion else 'desactivado'}[/bold yellow]")
            time.sleep(1)  # Corregido: añadir tiempo de espera
        elif key in ('\x1b[a', 'w'):
            if selected_index > 0:
                selected_index -= 1
                if selected_index < scroll_offset:
                    scroll_offset = selected_index
        elif key in ('\x1b[b', 's'):
            if selected_index < len(items) - 1:
                selected_index += 1
                if selected_index >= scroll_offset + max_visible_items:
                    scroll_offset += 1
        elif key == '\r':
            if items:
                selected_item, is_dir = items[selected_index]
                if is_dir:
                    new_folder = os.path.normpath(os.path.join(current_folder, selected_item))
                    if os.path.isdir(new_folder):
                        current_folder = new_folder
                        selected_index = 0
                        scroll_offset = 0
                        saved_music_files = []  # Resetear lista al cambiar de carpeta
                else:
                    saved_music_files = [item[0] for item in items 
                                      if not item[1] and item[0].lower().endswith((".mp3", ".wav"))]
                    try:
                        current_music_index = saved_music_files.index(selected_item)
                    except ValueError:
                        current_music_index = -1
                    
                    song_path = os.path.join(current_folder, selected_item)
                    if current_song_path:
                        stop_music()
                    current_song_path = song_path
                    total_duration = get_music_length(song_path)
                    start_time = time.time()
                    paused = False
                    play_music(song_path)
        elif key == ' ':
            if current_song_path:
                if paused:
                    unpause_music()
                    start_time = time.time() - paused_position
                    paused = False
                else:
                    pause_music()
                    paused_position = time.time() - start_time
                    paused = True
        elif key in ('\x1b[d', 'a'):
            if current_song_path:
                current_pos = paused_position if paused else (time.time() - start_time)
                new_pos = max(0, current_pos - 5)
                if paused:
                    paused_position = new_pos
                else:
                    pygame.mixer.music.stop()
                    pygame.mixer.music.play(start=new_pos)
                    start_time = time.time() - new_pos
        elif key in ('\x1b[c', 'd'):
            if current_song_path:
                current_pos = paused_position if paused else (time.time() - start_time)
                new_pos = min(total_duration, current_pos + 5)
                if paused:
                    paused_position = new_pos
                else:
                    pygame.mixer.music.stop()
                    pygame.mixer.music.play(start=new_pos)
                    start_time = time.time() - new_pos
        elif key == 'z':
            if current_song_path:
                stop_music()
                current_song_path = None
                paused = False
                current_music_index = -1
        elif key in ('+', '='):
            set_volume(0.1)
        elif key == '-':
            set_volume(-0.1)
        elif key in ('\x1b', 'q'):
            opacidad.restore_configurations()
            if current_song_path:
                stop_music()
            break

        # Detección de fin de canción (dentro del bucle principal)
        if current_song_path and not paused and not pygame.mixer.music.get_busy():
            if autoreproduccion and current_music_index != -1:
                next_index = current_music_index + 1
                if next_index < len(saved_music_files):
                    next_song = saved_music_files[next_index]
                    song_path = os.path.join(current_folder, next_song)
                    
                    if os.path.exists(song_path):
                        current_music_index = next_index
                        current_song_path = song_path
                        total_duration = get_music_length(song_path)
                        start_time = time.time()
                        paused = False
                        play_music(song_path)
                else:
                    current_song_path = None
                    paused = False
                    current_music_index = -1
                    
if __name__ == "__main__":
    music_player(default_music_folder)