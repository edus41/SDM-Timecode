from multiprocessing import Process, Pipe
from server import *
from gui import *
from player import *

##############################################
##------------------ MAIN ------------------##
##############################################

if __name__ == "__main__":
    gui_pipe, server_pipe = Pipe()
    gui_pipe2, player_pipe = Pipe()
    
    server = Network(gui_pipe)
    player = Player(gui_pipe2)
    gui = Process(target = UI, args = (server_pipe,player_pipe))
    
    server.start()
    player.start()
    gui.start()
    
    while True:
        if not gui.is_alive():
            server.terminate()
            player.terminate()
            server.join()
            player.join()
            break
        time.sleep(1)

