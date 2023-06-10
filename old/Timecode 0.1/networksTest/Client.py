import socket
import threading
import time
import json
from queue import Queue

class Cliente:
    def __init__(self, host='localhost', puerto=8080):
        self.host = host
        self.puerto = puerto
        self.socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ultimo_mensaje = ""
        self.conectado = False

    def conectar(self):
        try:
            self.socket_cliente.connect((self.host, self.puerto))
            self.conectado = True
            print(f"Conexión establecida con el servidor: {self.host}:{self.puerto}")
            threading.Thread(target=self._recibir_mensajes).start()

        except socket.error as e:
            print(f"Error al conectar con el servidor: {str(e)}")
            self.conectado = False

    def _recibir_mensajes(self):
        while self.conectado:
            try:
                mensaje = self.socket_cliente.recv(1024).decode('utf-8')
                self.ultimo_mensaje = mensaje

                # Convertir la cadena JSON en un diccionario
                mensaje_dict = json.loads(mensaje)

                # Manejar el mensaje recibido
                self._manejar_mensaje(mensaje_dict)

            except socket.error as e:
                if e.errno == 10054:
                    print("Conexión cerrada por el host remoto. Desconectando...")
                    self.conectado = False
                else:
                    print(f"Error al recibir mensaje: {str(e)}")
                    self.conectado = False

    def enviar_mensaje(self, mensaje):
        if self.conectado:
            try:
                mensaje_json = json.dumps(mensaje)  # Convertir el diccionario en una cadena JSON
                self.socket_cliente.send(mensaje_json.encode('utf-8'))
            except socket.error as e:
                print(f"Error al enviar mensaje: {str(e)}")
        else:
            print("El cliente no está conectado. No se pudo enviar el mensaje.")

    def detener(self):
        self.conectado = False
        self.socket_cliente.close()