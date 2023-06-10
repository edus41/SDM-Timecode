import socket
from _thread import *
from threading import Thread, Event
import time
# Colores ANSI
RESET = "\033[0m"  # Restablece todos los atributos y colores
BOLD = "\033[1m"  # Texto en negrita
UNDERLINE = "\033[4m"  # Texto subrayado

# Colores de texto
BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"


class Servidor():
    def __init__(self, host="127.0.0.1", port=1233):
        self.host = host
        self.port = port
        self.socket_servidor = None
        self.clientes_conectados = []
        self.online = False

    def iniciar(self,event:Event) -> None:
        while not self.online:
            if event.is_set():
                print(GREEN + f"[SERVER WAS STOPED] {self.host}:{self.port}"+RESET)
                break
            try:
                self.socket_servidor = socket.socket()
                self.socket_servidor.bind((self.host, self.port))
                self.socket_servidor.listen(5)
                self.online = True
                print(GREEN + f"[SERVER STABLISH] {self.host}:{self.port}"+RESET)

                while self.online:
                    try:
                        client, address = self.socket_servidor.accept()
                        start_new_thread(self._client_thread, (client,event))
                        self.clientes_conectados.append(client)
                        print(GREEN+"[NEW CLIENT CONNECTED] " + address[0] + ":" + str(address[1])+RESET)
                    except socket.error as e:
                        print(GREEN+"[ERROR DE CONEXIÓN DE CLIENTE]: " + str(e)+RESET)

            except socket.error as e:
                self.online = False
                self.socket_servidor = None
                print(GREEN+"[ERROR]: " + str(e)+RESET)

    def _client_thread(self, cliente,event):
            try:
                client_adress=cliente.getpeername()
                cliente.send(str.encode(f"WELCOME {client_adress}"))
                while True:
                    if event.is_set():
                        print(GREEN + f"[SERVER WAS STOPED] {self.host}:{self.port}"+RESET)
                        break
                    try:
                        data = cliente.recv(1024)
                        if not data:
                            break
                        client_message=data.decode("utf-8")
                        
                        print(GREEN+f"{client_adress}: {client_message}"+RESET)
                        reply = "Hello, I am the server, and you said: " + data.decode("utf-8")
                        cliente.sendall(str.encode(reply))
                    except socket.error as e:
                        print(GREEN+"[CLIENT DISCONNECTED]: Failed to send/receive message: " + str(e)+RESET)
                        break
            except socket.error as e:
                print(GREEN+"[CLIENT DISCONNECTED]: Failed to send welcome message: " + str(e)+RESET)
            finally:
                self.clientes_conectados.remove(cliente)
                cliente.close()
    
    def enviar_mensaje_a_todos(self,mensaje):
        
        for client in self.clientes_conectados:
                client.sendall(str.encode(mensaje))
    
    def detener(self):
        self.online = False
        if self.socket_servidor:
            try:
                self.socket_servidor.close()
            except socket.error as e:
                print(BLUE + "[ERROR AL CERRAR EL SOCKET]: " + str(e) + RESET)
            finally:
                self.socket_servidor = None
                
    def __del__(self):
        self.detener()


#----------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------#

class Cliente:
    def __init__(self, host="127.0.0.1", port=1233):
        self.host = host
        self.port = port
        self.socket_cliente = None
        self.conectado = False

    def iniciar(self,event:Event):
        while not self.conectado:
            if event.is_set():
                print(BLUE + f"[CLIENT WAS STOPED] {self.host}:{self.port}"+RESET)
                break
            try:
                self.socket_cliente = socket.socket()
                self.socket_cliente.connect((self.host, self.port))
                self.conectado = True
                print(BLUE + f"[CONNECTED TO SERVER] {self.host}:{self.port}"+RESET)

                while self.conectado:
                    try:
                        self.socket_cliente.send(str.encode("Ping"))
                        response = self.socket_cliente.recv(1024)
                        if response:
                            message = response.decode()
                            server_adress=self.socket_cliente.getpeername()
                            print(BLUE+f"[SERVIDOR {server_adress} TE DICE]: {message}"+RESET)
                            time.sleep(0.5)
                    except socket.error as e:
                        self.conectado = False
                        self.socket_cliente = None
                        print(BLUE+"[ERROR AL ENVIAR MENSAJE AL SERVIDOR]: " + str(e)+RESET)
                        break
                                        
            except socket.error as e:
                print(BLUE+f"[NINGUN SERVIDOR ENCONTRADO EN {self.host}:{self.port} ]: " + str(e)+RESET)
                self.conectado = False
                self.socket_cliente = None
    
    def detener(self):
        self.conectado = False
        if self.socket_cliente:
            try:
                self.socket_cliente.close()
            except socket.error as e:
                print(BLUE + "[ERROR AL CERRAR EL SOCKET]: " + str(e) + RESET)
            finally:
                self.socket_cliente = None

        
    def __del__(self):
        self.detener()