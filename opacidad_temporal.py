import os
import json
import subprocess
import winreg
import shutil
import sys

#Variables Globales
relative_path = os.path.join("sources", "img", "black_bg.png")
absolute_path = ""
opacity = 100
# se planea cambiar esto a futuro
background_image = absolute_path

def resource_path(relative_path):
    """ Get Absolute path to resource, works for dev and PyInstaller"""
    try:
        base_path= sys.MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.abspath(".")


# Devuelve una ruta absoluta de una ruta relativa
def get_absolute_path(relative_path: str) -> str:
    """
    Convierte una ruta relativa en una ruta absoluta.
    
    :param relative_path: Ruta relativa a convertir.
    :return: Ruta absoluta correspondiente.
    """
    return os.path.abspath(relative_path)

absolute_path = get_absolute_path(relative_path)
background_image = resource_path(relative_path)
def detect_environment():
    """Detecta si el entorno es Windows Terminal, PowerShell o CMD."""
    if "WT_SESSION" in os.environ:
        return "WindowsTerminal"
    try:
        subprocess.run(["powershell", "-Command", "$PSVersionTable"], capture_output=True, text=True, check=True)
        return "PowerShell"
    except:
        return "CMD"

def backup_file(file_path):
    """Crea una copia de seguridad del archivo antes de modificarlo."""
    backup_path = file_path + ".backup"
    if os.path.exists(file_path):
        shutil.copy(file_path, backup_path)
    return backup_path

def restore_file(file_path):
    """Restaura la configuración desde la copia de seguridad."""
    backup_path = file_path + ".backup"
    if os.path.exists(backup_path):
        shutil.copy(backup_path, file_path)
        os.remove(backup_path)

def modify_windows_terminal(json_path):
    """Modifica el archivo settings.json de Windows Terminal."""
    backup_file(json_path)
    
    if not os.path.exists(json_path):
        print("❌ No se encontró el archivo JSON.")
        return
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            settings = json.load(f)

        modified = False
        

        for profile in settings.get("profiles", {}).get("list", []):
            if "opacity" in profile:
                profile["opacity"] = opacity
                modified = True

        defaults = settings.setdefault("profiles", {}).setdefault("defaults", {})
        
        if defaults.get("opacity", None) != opacity:
            defaults["opacity"] = opacity
            modified = True

        if defaults.get("useAcrylic", False):
            defaults["useAcrylic"] = False
            modified = True

        if defaults.get("backgroundImage", None) != background_image:
            defaults["backgroundImage"] = background_image
            defaults["backgroundImageStretchMode"] = "fill"
            modified = True

        if modified:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4, ensure_ascii=False, sort_keys=True)
            print("✅ Configuración de Windows Terminal modificada correctamente.")

    except json.JSONDecodeError as e:
        print(f"⚠️ Error de JSON: {e}")
    except Exception as e:
        print(f"⚠️ Error: {e}")

def modify_powershell_profile():
    """Aplica cambios de fondo y título en PowerShell solo en la sesión actual."""
    try:
        subprocess.run(["powershell", "-Command",
            "$Host.UI.RawUI.BackgroundColor = 'Black';"
            "$Host.UI.RawUI.WindowTitle = 'PowerShell Temporal';"
        ], shell=True)
        print("✅ Configuración temporal de PowerShell aplicada.")
    except Exception as e:
        print(f"⚠️ Error al modificar PowerShell: {e}")

def modify_cmd_registry():
    """Aplica cambios de opacidad en CMD solo en la sesión actual."""
    try:
        hwnd = subprocess.run(["powershell", "-Command", 
            "(Get-Process -Id $PID).MainWindowHandle"
        ], capture_output=True, text=True).stdout.strip()

        if hwnd.isdigit():
            subprocess.run(["powershell", "-Command",
                f"[void] [System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms');"
                f"$wshell = New-Object -ComObject wscript.shell;"
                f"$wshell.SendKeys('% ');"
            ], shell=True)
            print("✅ Configuración temporal de CMD aplicada.")
        else:
            print("⚠️ No se pudo obtener el identificador de la ventana de CMD.")
    except Exception as e:
        print(f"⚠️ Error al modificar CMD: {e}")

def restore_configurations():
    """Restaura todas las configuraciones originales al cerrar el programa."""
    environment = detect_environment()
    
    if environment == "WindowsTerminal":
        json_file_path = os.path.join(os.environ["LOCALAPPDATA"], "Packages", "Microsoft.WindowsTerminal_8wekyb3d8bbwe", "LocalState", "settings.json")
        restore_file(json_file_path)
        print("✅ Configuración de Windows Terminal restaurada.")
    #elif environment == "PowerShell":
    #    profile_path = os.path.expandvars("$PROFILE")
    #    restore_file(profile_path)
    #    print("✅ Configuración de PowerShell restaurada.")
    #elif environment == "CMD":
    #    print("⚠️ Restauración del registro de CMD no implementada automáticamente. Debe restaurarse manualmente.")

def main():
    environment = detect_environment()
    if environment == "WindowsTerminal":
        json_file_path = os.path.join(os.environ["LOCALAPPDATA"], "Packages", "Microsoft.WindowsTerminal_8wekyb3d8bbwe", "LocalState", "settings.json")
        modify_windows_terminal(json_file_path)
    elif environment == "PowerShell":
        modify_powershell_profile()
    elif environment == "CMD":
        modify_cmd_registry()
    else:
        print("❌ Entorno no identificado.")
    input("Presiona Enter para restaurar la configuración original...")
    restore_configurations()

if __name__ == '__main__':
    main()