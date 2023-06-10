from network2 import *
from threading import Thread,Event
import time

class Server():
    def __init__(self):
        self.sv_stop = Event()
        self.sv = Servidor(host="127.0.0.1", port=1233)
        
    def start(self):
        self.sv_thread = Thread(target=self.sv.iniciar, args=(self.sv_stop,))
        self.sv_thread.start()
        
    def send_to_all(self,mensaje):
        self.sv.enviar_mensaje_a_todos(mensaje)
        
    def stop(self):
        self.sv.detener()
        self.sv_stop.set()
        self.sv_thread.join()

class Client():
    def __init__(self):
        self.cli_stop = Event()
        self.cli = Cliente(host="127.0.0.1", port=1233)
        
    def start(self):
        self.cli_thread = Thread(target=self.cli.iniciar, args=(self.cli_stop,))
        self.cli_thread.start()
        
    def stop(self):
        self.cli.detener()
        self.cli_stop.set()
        self.cli_thread.join()
        
# TEST CONJUNTO
mi_cliente=Client()
mi_cliente.start()
mi_server=Server()
mi_server.start()

i = 0
while i<5:
    mi_server.send_to_all(f"{i}")
    i+=1
    time.sleep(0.5)

print("termino el ciclo")

mi_server.stop()
time.sleep(5)
mi_cliente.stop()

###TEST Cliente
#mi_cliente=Client()
#mi_cliente.start()

#i=0
#while i<11:
#    print(i)
#    i+=1
#    time.sleep(0.5)

#mi_cliente.stop()

###TEST Servidor
#mi_server=Server()
#mi_server.start()

#i=0
#while i<11:
#    print(i)
#    mi_server.send_to_all(i)
#    i+=1
#    time.sleep(0.5)

#mi_server.stop()


