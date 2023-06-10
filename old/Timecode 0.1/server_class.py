import time
from socket import *
from threading import Thread, current_thread,Event
from logs_tools import *

class Server():
    def __init__(self, host="127.0.0.1", port=12345):
        self.host = host
        self.port = port
        self.direccion = f"{host}:{port}"
        self.online = False
        self.s = None
        self.clientes_conectados = []
        self.data=""
        self.send_event = Event()
        self.stop_event = Event()
        
    def start(self):
        self.stop_event.clear()
        self.server_thread: Thread = Thread(target = self._conect)
        self.server_thread.start()
        
    def _conect(self):
        while not self.online:
            if self.stop_event.is_set():
                break
            try:
                self.s = socket(AF_INET, SOCK_STREAM)
                self.s.bind((self.host, self.port))
                log(f"[SERVER START ON]: {self.direccion}", GREEN)
                self.s.listen(5)
                log(f"[SERVER BROADCASTING ON]: {self.direccion}", GREEN)
                self.online = True
                self.send_event.clear()
                
                while self.online:
                    client, address = self.s.accept()
                    log(f"[CLIENTE CONECTADO]: {address}", GREEN)
                    self.clientes_conectados.append(client)
                    self.sender_thread: Thread = Thread(target = self._sender, args=(client,address))
                    self.sender_thread.start()
                    
            except Exception as e:
                if e.errno == 10048:
                    log(f"[SERVER ERROR]: Ya Existe Un Servidor Iniciado en: {self.direccion}, Reintentando...", RED)
                elif e.errno==10038:
                    log(f"[SERVER DISCONECTED]: Stop Event", RED)
                else:
                    log(f"[SERVER DISCONECTED]: {e}", RED)
                self.online = False
                time.sleep(1)

    def _sender(self,conexion,address):
        while self.online:
            if self.stop_event.is_set():
                conexion.close()
                break
            if self.send_event.is_set():
                try:
                    data_str=str(self.data)
                    conexion.send(bytes(data_str, "utf-8"))
                    self.send_event.clear()
                except Exception as e:
                    self.clientes_conectados.append(client)
                    log(f"[CLIENTE {address} DESCONECTADO]: {e}", RED)
                    self.send_event.clear()
                    break 
                
    def send_to_all(self,message):
        self.data = message
        self.send_event.set()
        
    def stop(self):
        self.online = False
        self.stop_event.set()
        if self.s:
            self.s.close()
            self.s = None
        log(f"[SERVER DICONECTED]: Stop Event", RED)
        
"""
server=Server()
server.start()

while True:
    data = {"fps": 25, "start_timecode": "00:00:00:00", "tc": "00:01:12:21", "is_playing": True}
    server.send_to_all(data)
    time.sleep(0.5)
"""