import time
from socket import *
from threading import Thread, current_thread,Event
from logs_tools import *

host="127.0.0.1"
port = 12345
direccion = f"{host}:{port}"
connected = False
stop_event = Event()

class ChatThread(Thread):
    
    def __init__(self, conexion):
        Thread.__init__(self)
        self.con = conexion
        global stop_event
        
    def run(self):
        name = current_thread().name
        while not stop_event.is_set():
            if name == "Sender":
                data = input("Enviar: ")
                try:
                    self.con.send(bytes(data, "utf-8"))
                except Exception as e:
                    log(f"[CONNECTION LOST]: No se Puedo Enviar el Mensaje", MAGENTA)
                    stop_event.set()
                    break

            elif name == "Receiver":
                try:
                    recData = self.con.recv(1024).decode()
                    if not recData:
                        log(f"[CONNECTION LOST 2]", MAGENTA)
                        self.con.close()
                        break
                    print("Server:", recData)
                except Exception as e:
                    log(f"[CONNECTION LOST 3]: {e}", MAGENTA)
                    self.con.close()
                    stop_event.set()
                    break
                
            


while not connected:
    try:
        client = socket()
        log(f"[CLIENT START]", CYAN)
        client.connect((host, port))    
        log(f"[CLIENT CONECTED]: {direccion}", CYAN)
        connected = True
        stop_event.clear()
        while True:
            
            sender = ChatThread(client)
            sender.name = "Sender"
            
            receiver = ChatThread(client)
            receiver.name = "Receiver"

            sender.start()
            receiver.start()

            sender.join()
            receiver.join()

            log(f"[SERVER UNAVAILABLE]: {direccion}", MAGENTA)
            client.close()
            connected = False
            
    except KeyboardInterrupt:
        break
    
    except Exception as e:
        if e.errno == 10061:
            log(f"[SERVER ERROR]: Ningun Servidor Disponible En: {direccion}, Reintentando...", MAGENTA)
        else:
            log(f"[SERVER ERROR]: {e}", MAGENTA)
        connected = False
        time.sleep(1)
    