import logging
import os
import sys
##############################################
##------------------ COLORS ----------------##
##############################################

GRIS_1_COLOR="#202020"
GRIS_2_COLOR="#777777"
GRIS_3_COLOR="#9FA1A0"
GRIS_4_COLOR="#AAAAAA"
GREEN_COLOR="#3DBC78"
RED_COLOR="#A52F2F"
YELLOW_COLOR="#BCB851"

##############################################
##------------------ LOG -------------------##
##############################################

# Configurar el registro de errores
username = os.getlogin()
log_dir = f'C:/users/{username}/.sdmtimecode'
os.makedirs(log_dir, exist_ok = True)
log_path = os.path.join(log_dir, 'logs.txt')
logging.basicConfig(filename=log_path, level=logging.INFO, encoding='utf-8', format='%(asctime)s - %(levelname)s - %(message)s')

ERROR = "ERROR"
INFO = "INFO"
WARNING = "WARNING"
CRITICAL = "CRITICAL"
DEBUG = "DEBUG"

BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"
RESET = "\033[0m"

def log(*messages, type="ERROR"):
    
    if messages and messages[-1] in (ERROR, INFO, WARNING, CRITICAL, DEBUG):
        type = messages[-1]
        messages = messages[:-1]
            
    message = " ".join(str(message) for message in messages)
    
    if type=="ERROR":
        print(RED + message + RESET)
        logging.error(message)
        
    elif type=="INFO":
        print(GREEN + message + RESET)
        logging.info(message)

    elif type=="WARNING":
        print(YELLOW + message + RESET)
        logging.warning(message)
        
    elif type=="CRITICAL":
        print(RED + message + RESET)
        logging.critical(message)
        
    elif type=="DEBUG":
        print(MAGENTA + message + RESET)
        logging.debug(message)

##############################################
##---------------- TIMECODE ----------------##
##############################################

def tc_to_secs(timecode, fps = 99):#OK
    horas, minutos, segundos, frames = map(int, timecode.split(":"))
    total_seconds = (horas * 3600) + (minutos * 60) + segundos + (frames / fps)
    return total_seconds

def secs_to_tc(seconds, fps = 99, type="str"):#OK
    hh = int(seconds / 3600)
    mm = int((seconds % 3600) / 60)
    ss = int(seconds % 60)
    ff = int((seconds * fps) % fps)
    if type == "str":
        return f"{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}"
    else:
        return [hh,mm,ss,ff]

##############################################
##------------------ PATHS -----------------##
##############################################

def resource_path(relative_path):
    """Obtiene la ruta absoluta al recurso, compatible con PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)