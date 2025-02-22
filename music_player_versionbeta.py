import os
import sys
import time
import pygame
import readchar
import textwrap
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, ProgressColumn, BarColumn, TaskProgressColumn, TextColumn

#Constantes NO MODIFICAR
MUSIC_PLAYER_NAME = "GingaPlayer (銀河プレーヤー)"
AUTOR = "LDTech"

# Configuración inicial
if os.name == 'nt':
    import msvcrt

console = Console()
default_music_folder = os.path.join(os.environ['USERPROFILE'], "Music") if os.name == "nt" else os.path.expanduser("~/Music")
max_visible_items = 10

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
def render_interface(songs, selected_index, scroll_offset):
    table = Table(border_style="red")
    table.add_column("#", justify="right", style="dim")
    table.add_column("Canción")
    
    for i in range(scroll_offset, min(len(songs), scroll_offset + max_visible_items)):
        style = "bright_cyan" if i == selected_index else "bright_green"
        table.add_row(str(i + 1), Text(songs[i], style=style))
    
    return table

def handle_arrow_keys(key):
    if key == '\x1b':
        seq = readchar.readkey()
        if seq == '[':
            seq += readchar.readkey()
        if seq == '[A':
            return 'up'
        elif seq == '[B':
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
def music_player(music_folder):
    pygame.init()
    songs = get_music_files(music_folder)
    
    if not songs:
        console.print("[bold red]No se encontraron archivos de música.[/bold red]")
        return
    
    selected_index = 0
    scroll_offset = 0
    
    while True:
        console.clear()
        console.print(f"[bold bright_white]Made by {AUTOR}[/bold bright_white]", justify="left")
        console.print(f"🎵 [bold bright_cyan]{MUSIC_PLAYER_NAME}[/bold bright_cyan] 🎵", justify="center")
        console.print("Controles:", "↑/W: Arriba", "↓/S: Abajo", "Enter: Reproducir", "+/-: Volumen", "ESC: Salir", sep=" | ")
        console.print(render_interface(songs, selected_index, scroll_offset))
        
        try:
            key = readchar.readkey()
            key = handle_arrow_keys(key)
        except KeyboardInterrupt:
            break
        
        if key in ('w', 'up') and selected_index > 0:
            selected_index -= 1
            if selected_index < scroll_offset:
                scroll_offset = selected_index
        elif key in ('s', 'down') and selected_index < len(songs) - 1:
            selected_index += 1
            if selected_index >= scroll_offset + max_visible_items:
                scroll_offset += 1
        elif key == '\r':
            song_path = os.path.join(music_folder, songs[selected_index])
            play_music(song_path)
            playback_menu(song_path)
        elif key in ('+', '='):
            set_volume(0.1)
        elif key == '-':
            set_volume(-0.1)
        elif key in ('\x1b', 'q'):
            stop_music()
            break

if __name__ == "__main__":
    music_player(default_music_folder)