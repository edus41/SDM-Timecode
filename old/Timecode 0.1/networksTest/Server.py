import socket
import threading
import time
import json
from queue import Queue


class Servidor:
    def __init__(self, host='localhost', puerto=8080):
        self.host = host
        self.puerto = puerto
        self.socket_servidor = None
        self.clientes_conectados = []
        self.cola_mensajes = Queue()
        self.servidor_activo = False

    def _iniciar(self):
        try:
            self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_servidor.bind((self.host, self.puerto))
            self.socket_servidor.listen(5)
            print(f"Servidor escuchando en {self.host}:{self.puerto}")
            self.servidor_activo = True

            threading.Thread(target=self._aceptar_conexiones).start()

        except socket.error as e:
            print(f"Error al iniciar el servidor: {str(e)}")
            self.servidor_activo = False

    def _aceptar_conexiones(self):
        while self.servidor_activo:
            try:
                cliente, direccion = self.socket_servidor.accept()
                self.clientes_conectados.append(cliente)
                print(f"Nueva conexión establecida: {direccion}")
                threading.Thread(target= self._procesar_cliente(cliente))

            except socket.error as e:
                print(f"Error al aceptar conexión de cliente: {str(e)}")
                break

    def _procesar_cliente(self, cliente):
        while self.servidor_activo:
            try:
                mensaje = cliente.recv(1024).decode('utf-8')
                if mensaje:
                    # Convertir la cadena JSON en un diccionario
                    mensaje_dict = json.loads(mensaje)

                    # Manejar el mensaje recibido
                    self._manejar_mensaje(cliente, mensaje_dict)

            except socket.error as e:
                print(f"Error al procesar cliente: {str(e)}")
                break

    def _manejar_mensaje(self, cliente, mensaje):
        # Procesar y responder el mensaje recibido
        if mensaje == "ping":
            respuesta = "¡Pong!"
            cliente.send(respuesta.encode('utf-8'))

        # Añadir el mensaje a la cola de mensajes para enviar a todos los clientes
        self.cola_mensajes.put((cliente, mensaje))

    def _enviar_mensajes(self, mensaje):
        while self.servidor_activo:
            # Enviar el mensaje a todos los clientes conectados
            for cliente_conectado in self.clientes_conectados:
                try:
                    # Convertir el mensaje en una cadena JSON
                    mensaje_json = json.dumps(mensaje)
                    cliente_conectado.send(mensaje_json.encode('utf-8'))
                except socket.error as e:
                    print(f"Error al enviar mensaje: {str(e)}")
                    cliente_conectado.close()
                    self.clientes_conectados.remove(cliente_conectado)


    def detener(self):
        self.servidor_activo = False
        self.socket_servidor.close()
        for cliente in self.clientes_conectados:
            cliente.close()
