from multiprocess import Process, Pipe
from Network import *
from GUI import *
from Player import *
from MTC_Sender import *
from LTC_Sender import *

def close(proceso):
    if proceso.is_alive():
        proceso.terminate()
        proceso.join()

##############################################
##------------------ MAIN ------------------##
##############################################

if __name__ == "__main__":
    try:
        multiprocess.freeze_support()
            
        gui_pipe, network_pipe = Pipe()
        gui_pipe2, player_pipe = Pipe()
        gui_pipe3, mtc_pipe = Pipe()
        gui_pipe4, ltc_pipe = Pipe()
        gui_pipe5, main_pipe = Pipe()
        
        server = Network(gui_pipe)
        player = Player(gui_pipe2)
        mtc = MTC_Sender(gui_pipe3)
        ltc = LTC_Sender(gui_pipe4)
        gui = Process(target = UI, args=(network_pipe, player_pipe, ltc_pipe, mtc_pipe,main_pipe))
        
        server.start()
        player.start()
        mtc.start()
        ltc.start()
        gui.start()

        while True:
            end = gui_pipe5.recv()
            if "finish" in end:
                close(server)
                close(player)
                close(mtc)
                close(ltc)
                close(gui)
                break
            time.sleep(1)
    except Exception as e:
        print(f"[MAIN ERROR]: {e}")