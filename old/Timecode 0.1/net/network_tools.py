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
        self.stop_event = Event()
        
    def start(self):
        self.stop_event.clear()
        self.thread = Thread(target=self._iniciar)
        self.thread.start()

    def _iniciar(self) -> None:
        while not self.online:
            if self.stop_event.is_set():
                print(GREEN + f"[SERVER STOPED] {self.host}:{self.port}"+RESET)
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
                        if not self.online:
                            break  # Salir del bucle si el servidor se detiene mientras se acepta una conexión
                        self.thread2 = Thread(target=self._client_thread,args=(client,))
                        self.thread2.start()
                        self.clientes_conectados.append(client)
                        print(GREEN+"[NEW CLIENT CONNECTED] " + address[0] + ":" + str(address[1])+RESET)
                    except socket.error as e:
                        print(GREEN+"[ERROR DE CONEXIÓN DE CLIENTE]: " + str(e)+RESET)

            except socket.error as e:
                self.online = False
                self.socket_servidor = None
                print(GREEN+"[ERROR]: " + str(e)+RESET)

    def _client_thread(self, cliente):
        try:
            client_adress = cliente.getpeername()
            cliente.send(str.encode(f"WELCOME {client_adress}"))
            while True:
                if self.stop_event.is_set():
                    print(GREEN + f"[SERVER STOPPED 2] {self.host}:{self.port}" + RESET)
                    cliente.close()  # Close the connection with the client
                    break
                try:
                    data = cliente.recv(1024)
                    if not data:
                        break
                    client_message = data.decode("utf-8")
                    print(GREEN + f"{client_adress}: {client_message}" + RESET)
                    reply = "Hello, I am the server, and you said: " + data.decode("utf-8")
                    cliente.sendall(str.encode(reply))
                except ConnectionAbortedError:
                    print(GREEN + "[CLIENT DISCONNECTED]: Connection aborted by the client" + RESET)
                    break
                except socket.error as e:
                    print(GREEN + "[CLIENT DISCONNECTED]: Failed to send/receive message: " + str(e) + RESET)
                    break
        except socket.error as e:
            print(GREEN + "[CLIENT DISCONNECTED]: Failed to send welcome message: " + str(e) + RESET)
        finally:
            if cliente in self.clientes_conectados:
                self.clientes_conectados.remove(cliente)
                if cliente:
                    try:
                        cliente.close()
                    except socket.error as e:
                        print(GREEN + "[ERROR AL CERRAR EL CLIENTE]: " + str(e) + RESET)

    
    def send_menssage_to_all(self,mensaje):
        print(GREEN+f"[ENVIANDO]:{mensaje}"+RESET)
        for client in self.clientes_conectados:
                client.send(str.encode(mensaje))
    
    def stop(self):
        self.online = False
        self.stop_event.set()
        for client in self.clientes_conectados:
            try:
                client.sendall(str.encode("[SERVER_STOPPED]"))
                client.close()
            except socket.error as e:
                print(GREEN + "[ERROR AL CERRAR EL CLIENTE]: " + str(e) + RESET)
        self.socket_servidor.close()
        self.thread.join()
        self.clientes_conectados = []
                
    def __del__(self):
        self.stop()


#----------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------#
#----------------------------------------------------------------------------------------------#

class Cliente:
    def __init__(self, host="127.0.0.1", port=1233):
        self.host = host
        self.port = port
        self.socket_cliente = None
        self.conectado = False
        self.stop_event = Event()
        
    def start(self):
            self.stop_event.clear()
            self.thread = Thread(target=self._iniciar)
            self.thread.start()
            
    def _iniciar(self):
        while not self.conectado:
            if self.stop_event.is_set():
                print(BLUE + f"[CLIENT STOPED] {self.host}:{self.port}"+RESET)
                break
            try:
                self.socket_cliente = socket.socket()
                self.socket_cliente.connect((self.host, self.port))
                self.conectado = True
                print(BLUE + f"[CONNECTED TO SERVER] {self.host}:{self.port}"+RESET)
                
                while self.conectado:
                    try:
                        response = self.socket_cliente.recv(1024)
                        if response:
                            message = response.decode()
                            if message == "[SERVER_STOPPED]":
                                print(BLUE + "[SERVIDOR DESCONECTADO]" + RESET)
                                self.conectado = False
                                self.socket_cliente.close()
                                break
                            server_adress = self.socket_cliente.getpeername()
                            print(BLUE + f"[SERVIDOR {server_adress} TE DICE]: {message}" + RESET)

                    except socket.error as e:
                        print(BLUE + "[SERVIDOR DESCONECTADO]: " + str(e) + RESET)
                        self.conectado = False
                        self.socket_cliente.close()
                        break
                                        
            except socket.error as e:
                print(BLUE + f"[NINGUN SERVIDOR ENCONTRADO EN {self.host}:{self.port} ]: " + str(e) + RESET)
                self.conectado = False
                self.socket_cliente = None
                break
                
    def stop(self):
        self.conectado = False
        self.stop_event.set()
        if self.socket_cliente:
            try:
                self.socket_cliente.close()
            except socket.error as e:
                print(BLUE + "[ERROR AL CERRAR EL SOCKET]: " + str(e) + RESET)
            finally:
                self.socket_cliente = None
        self.thread.join()

        
    def __del__(self):
        self.stop()

