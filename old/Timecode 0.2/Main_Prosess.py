# funcion que recibe intrucciones de una UI para:
# reproducir ltc si esta habilitado
# reproducir mtc si esta habilitado
# crear servidor y enviar informacion si esta habilitado
# conectarse con servidor y recivir info si esta habilitado

##la GUI solo recibe timecode, status de red, numero de clientes conectados,
from Player_Prosess import Player
import time

if __name__ == "__main__":
    player = Player()
    # player.open_audio_file("C:\\Users\\Eduardo Rodriguez\\Desktop\\audio.wav")
    # player.set_start_time("00:01:00:00")
    # player.set_end_time("00:01:05:00")
    time.sleep(1)
    print("ready")
    player.start()
    time.sleep(5)
    player.stop()
