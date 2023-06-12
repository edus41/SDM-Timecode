from multiprocessing import Process, Pipe
from Network import *
from GUI import *
from Player import *
from MTC_Sender import *
from LTC_Sender import *

##############################################
##------------------ MAIN ------------------##
##############################################

if __name__ == "__main__":
    gui_pipe, network_pipe = Pipe()
    gui_pipe2, player_pipe = Pipe()
    gui_pipe3, mtc_pipe = Pipe()
    gui_pipe4, ltc_pipe = Pipe()
    
    server = Network(gui_pipe)
    player = Player(gui_pipe2)
    mtc = MTC_Sender(gui_pipe3)
    ltc = LTC_Sender(gui_pipe4)
    gui = Process(target = UI, args=(network_pipe, player_pipe, ltc_pipe, mtc_pipe))
    
    server.start()
    player.start()
    mtc.start()
    ltc.start()
    gui.start()
    
    while True:
        if not gui.is_alive():
            server.terminate()
            player.terminate()
            server.join()
            player.join()
            break
        time.sleep(1)
