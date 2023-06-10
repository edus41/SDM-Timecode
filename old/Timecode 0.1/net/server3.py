import time
from socket import *
from threading import Thread, current_thread
from logs_tools import *

class ChatThread(Thread):
    def __init__(self, conexion):
        Thread.__init__(self)
        self.con = conexion

    def run(self):
        name = current_thread().name
        while True:
            if name == "Sender":
                data = input("Enviar: ")
                try:
                    self.con.send(bytes(data, "utf-8"))
                except Exception as e:
                    log(f"[CONNECTION LOST]: {e}", RED)
                    break

            elif name == "Receiver":
                try:
                    recData = self.con.recv(1024).decode()
                    if not recData:
                        log(f"[CONNECTION LOST 2]", RED)
                        self.con.close()
                        break
                    print("Server:", recData)
                except Exception as e:
                    log(f"[CONNECTION LOST 3]: {e}", RED)
                    self.con.close()
                    break
                
                
host="127.0.0.1"
port = 12345
direccion = f"{host}:{port}"
online = False
connections = []

while not online:
    try:
        s = socket(AF_INET, SOCK_STREAM)
        s.bind((host, port))
        log(f"[SERVER START ON]: {direccion}", GREEN)
        s.listen(5)
        log(f"[SERVER LISTENING ON]: {direccion}", GREEN)
        online = True
        while True:
                    connection, address = s.accept()
                    connections.append(connection)
                    sender = ChatThread(connection)
                    sender.name = "Sender"
                    receiver = ChatThread(connection)
                    receiver.name = "Receiver"
                    sender.start()
                    receiver.start()
    except KeyboardInterrupt:
        break
    except Exception as e:
        if e.errno == 10048:
            log(f"[SERVER ERROR]: Ya Existe Un Servidor Iniciado en: {direccion}, Reintentando...", RED)
        else:
            log(f"[SERVER ERROR]: {e}", RED)
        online = False
        time.sleep(1)
    