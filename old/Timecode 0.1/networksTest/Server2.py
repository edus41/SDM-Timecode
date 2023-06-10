import socket
import threading

class Servidor:
    def __init__(self, host='localhost', port=6879):
        self.host = host
        self.port = port
        self.iniciado = False
        self.clientes = []
        self.detener_solicitud = threading.Event()

    def iniciar(self):  
        threading.Thread(target=self._open).start()                   

    def _open(self):
        while not self.iniciado and not self.detener_solicitud.is_set():
            try:
                self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket_servidor.bind((self.host, self.port))
                self.socket_servidor.listen(5)
                self.iniciado = True
                print("Servidor iniciado. Esperando conexiones...")
            
                threading.Thread(target=self._aceptar_conexiones).start()                   
                
            except Exception as e:
                print(f"[ERROR AL INICIAR]: Reintentando en 1 segundo")
                self.iniciado = False
                
    def _aceptar_conexiones(self):
        while self.iniciado:
            try:
                cliente_socket, cliente_direccion = self.socket_servidor.accept()
                self.clientes.append(cliente_socket)
                threading.Thread(target=self.manejar_cliente, args=(cliente_socket,)).start()
                print(f"[CLIENTE CONECTADO]: {cliente_socket}")

            except socket.error as e:
                print(f"[UN CLIENTE NO SE PUDO CONECTAR] {str(e)}")
                break
           
    def manejar_cliente(self, cliente_socket):
        while self.iniciado:
            try:
                mensaje = cliente_socket.recv(1024)
                if mensaje:
                    mensaje_decodificado = mensaje.decode()
                    print(f"[CLIENTE {cliente_socket}, MENSAJE]: {mensaje_decodificado}")
                    self.enviar_mensaje_a_todos(mensaje_decodificado)
            except Exception as e:
                print(f"[CLIENTE DESCONECTADO]: {cliente_socket}")
                if cliente_socket in self.clientes:
                    self.clientes.remove(cliente_socket)
                cliente_socket.close()
                break


          
    def enviar_mensaje_a_todos(self, mensaje):
        mensaje_str = str(mensaje)  # Convertir el diccionario a una cadena de texto
        for cliente_socket in self.clientes:
            try:
                print("[SEND MESSAGE]:", mensaje)
                cliente_socket.send(mensaje_str.encode())
            except Exception as e:
                print("[ERROR]: al enviar el mensaje:", str(e))

    def detener(self):
        if self.detener_solicitud.set():
            None
        self.detener_solicitud.set()
        if self.iniciado:
            self.socket_servidor.close()
            self.iniciado = False

            for cliente_socket in self.clientes:
                cliente_socket.close()
            self.clientes = []
        
    def __del__(self):
        self.detener()
        
# Ejemplo de uso

servidor = Servidor('localhost', 1234)
servidor.iniciar()


