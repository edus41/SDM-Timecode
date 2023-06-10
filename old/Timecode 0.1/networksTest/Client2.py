import socket
import threading
import time

class Cliente:
    def __init__(self, host='localhost', port=6879):
        self.host = host
        self.port = port
        self.ultimo_mensaje = ""
        self.conectado = False
        self.online = False
        self.detener_solicitud = threading.Event()

    def conectar(self):
        if not self.online:
            threading.Thread(target=self._open).start()
        else:
            print("El cliente ya está conectado.")
            
    def _open(self):
        while not self.conectado and not self.detener_solicitud.is_set():
            try:
                self.socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket_cliente.connect((self.host, self.port))
                print("-------------------------------------------------")
                print(f"[CONECTADO AL SERVIDOR]: {self.socket_cliente}")
                self.conectado = True
                self.online = True
                threading.Thread(target=self.recibir_mensajes).start()
            except ConnectionRefusedError as e:
                print("-------------------------------------------------")
                print("[SERVIDOR NO ACCESSIBLE]: Reintentando en 1 segundo...")
                print(str(e))
                self.online = True
                self.conectado = False
            except OSError:
                print("por qui")
                self.conectado = False
                self.online = False

    def recibir_mensajes(self):
        while self.conectado:
            try:
                mensaje = self.socket_cliente.recv(1024)
                if mensaje:
                    mensaje_decodificado = mensaje.decode()
                    mensaje_dict = eval(mensaje_decodificado)  # Convertir la cadena de texto a un diccionario
                    self.ultimo_mensaje = mensaje_dict
                    print("[SERVER MESSAGE]:", self.ultimo_mensaje)

            
            except ConnectionAbortedError:
                print("-------------------------------------------------")
                print("[CONEXIÓN ABORTADA]: La conexión ha sido cerrada por el servidor.")
                break  # Salir del bucle cuando se produce una conexión abortada

            except Exception as e:
                print("-------------------------------------------------")
                print("[SERVIDOR DESCONECTADO]: Intentando conectar en 1 segundo...")
                print(str(e))
                break  # Salir del bucle cuando se produce otra excepción

        self.conectado = False
        self.conectar()  # Reconectar después de salir del bucle

    def enviar_mensaje(self, mensaje):
        try:
            mensaje_str = str(mensaje)  # Convertir el mensaje a una cadena de texto
            self.socket_cliente.send(mensaje_str.encode())
        except Exception as e:
            print("Error al enviar el mensaje:", str(e))

    def detener(self):
        if self.conectado or self.online or not self.detener_solicitud.is_set():
            self.conectado = False
            self.online = False
            self.detener_solicitud.set()
            try:
                self.socket_cliente.close()

            except Exception as e:
                print("Error al cerrar el socket:", str(e))
                
                
                
cliente = Cliente()
cliente.conectar()
#cliente.detener()
