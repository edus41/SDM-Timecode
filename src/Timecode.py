from multiprocessing import Process, Pipe, freeze_support
from Network import *
from GUI import UI
from Player import Player
from MTC_Sender import MTC_Sender
from LTC_Sender import LTC_Sender
from Loading_GUI import loading_window

def close(proceso):
    if proceso.is_alive():
        proceso.terminate()
        proceso.join()
    
##############################################
##------------------ MAIN ------------------##
##############################################

if __name__ == "__main__":

    try:
        freeze_support()

        loading_process = Process(target = loading_window)
        loading_process.start()
            
        gui_pipe, network_pipe = Pipe()
        gui_pipe2, player_pipe = Pipe()
        gui_pipe3, mtc_pipe = Pipe()
        gui_pipe4, ltc_pipe = Pipe()
        gui_pipe5, main_pipe = Pipe()
        
        time.sleep(1)
        
        gui = Process(target = UI, args=(network_pipe, player_pipe, ltc_pipe, mtc_pipe,main_pipe))
        server = Network(gui_pipe)
        player = Player(gui_pipe2)
        mtc = MTC_Sender(gui_pipe3)
        ltc = LTC_Sender(gui_pipe4)
        
        
        server.start()
        player.start()
        mtc.start()
        ltc.start()
        gui.start()

        while True:
            end = gui_pipe5.recv()
            if "loading" in end:
                close(loading_process)
            if "finish" in end:
                close(server)
                close(player)
                close(mtc)
                close(ltc)
                close(gui)
                break
            time.sleep(1)
            
    except Exception as e:
        log(f"[MAIN ERROR]: {str(e)}")
        