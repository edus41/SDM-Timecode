from multiprocess import Process
import multiprocess
from threading import Thread
import time
from socket import *
from tools import *

##############################################
##---------------- THREADS -----------------##
##############################################

class ClienteHilo(Thread):
    def __init__(self, cliente):
        Thread.__init__(self)
        self.cliente = cliente

    def run(self):
        try:
            while True:
                mensaje_recibido = self.cliente.recv(1024).decode("utf-8")
                
                if mensaje_recibido:
                    log(f"[ClienteHilo {self.cliente}]: {mensaje_recibido}",GREEN)

        except ConnectionResetError:
            log(F"[ERROR ClienteHilo]: Cliente {self.cliente} desconectado abruptamente.",RED)
        
        except Exception as e:
            log(f"[ERROR ClienteHilo]: {e}", RED)

##############################################
##---------------- NETWORK -----------------##
##############################################

class Network(Process):

    def __init__(self, network_pipe):
        Process.__init__(self)
        
        # privates
        self.is_running = True
        self.pipe = network_pipe
        self.last_timecode = 0
        self.server = None
        self.client = None
        
        # to recive
        self.host = "Networks not found"
        self.port = 44444
        self.network_is_on = False
        self.timecode = 0
        self.direccion = f"{self.host}:{self.port}"
        self.server_address = (self.host, self.port)
        self.mode = "master"
        
        # to send
        self.online = False
        self.error = None
        self.clients = []
        
        #client mode
        self.timecode_recv = 0

    def run(self):
        
        self.recive_thread = Thread(target = self.recive_data)
        self.recive_thread.start()
        
        self.send_thread = Thread(target = self.send_data)
        self.send_thread.start()
        
        self.update_clients_thread = Thread(target=self.update_clients)
        self.update_clients_thread.start()
        
        while self.is_running:
            
            self.clients = []
            
            if self.host != "Networks not found":
                self.run_server()
                self.run_client()
                
                self.online = False
                self.error = None
                
                if self.server is not None:
                    self.stop_server()  
                    
                if self.client is not None:
                    self.stop_client() 

            time.sleep(0.1)

    def run_server(self):
        while not self.online and self.network_is_on and self.mode == "master":
            try:
                self.server = socket(AF_INET, SOCK_STREAM)
                self.server.bind((self.host, self.port))
                self.server.listen(5)
                time.sleep(1)
                self.online = True
                self.error = None
                
                log(f"[SERVER INIT] Esperando conexiones en {self.host}:{self.port}", GREEN)

                while self.online and self.network_is_on and self.mode == "master":
                    cliente, direccion = self.server.accept()
                    log(f"[CLIENT CONECT] {direccion[0]}:{direccion[1]} conectado.", GREEN)

                    cliente_hilo = ClienteHilo(cliente)
                    cliente_hilo.start()
                    self.clients.append(cliente)

                if not self.network_is_on:
                        break    

            except Exception as e:
                if "10048" in str(e):
                    log(f"[SERVER ERROR]: Ya Existe Un Servidor Iniciado en: {self.direccion}, Reintentando...", RED)
                    self.error = "NETWORK NOT AVIABLE"
                elif "11001" in str(e):
                    log(f"[SERVER ERROR]: IP FORMAT INVALID {e}", RED)
                    self.error = "IP FORMAT INVALID"
                elif "10049" in str(e):
                    log(f"[SERVER ERROR]: INVALID IP {e}", RED)
                    self.error = "INVALID IP"
                elif "10038" in str(e):
                    log(f"[SERVER DISCONECTED]: Stop Event, {e}", RED)
                    self.error = None
                elif "0-65535" in str(e):
                    log(f"[SERVER ERROR]: Stop Event, {e}", RED)
                    self.error = "PORT MUST BE 0-65535"
                else:
                    log(f"[SERVER ERROR]: {e}", RED)
                    self.error = "SERVER ERROR"
                self.online = False
                self.server = None

    def run_client(self):
        while not self.online and self.network_is_on and self.mode == "slave":
            try:
                self.client = socket(AF_INET, SOCK_STREAM)
                self.client.connect((self.host, self.port))
                log("Conectado al servidor {}:{}".format(self.host, self.port),GREEN)
                time.sleep(1)
                self.online = True
                self.error = None
                
                while self.online and self.network_is_on and self.mode == "slave":
                    data = self.client.recv(1024).decode("utf-8")
                    if data != " ":
                        self.timecode_recv = float(data)
                    
            except Exception as e:
                if "10048" in str(e):
                    log(f"[CLIENT ERROR]: Failed to open connection on port {self.port} {e}", MAGENTA)
                    self.error = None
                elif "10054" or "10061" in str(e):
                    log(f"[CLIENT ERROR]: not server found {e}", MAGENTA)
                    self.error = "SERVER NOT FOUND"
                elif "11001" in str(e):
                    log(f"[CLIENT ERROR]: INVALID IP FORMAT {e}", MAGENTA)
                    self.error = "INVALID IP FORMAT"
                elif "10049" in str(e):
                    log(f"[CLIENT ERROR]: INVALID IP {e}", MAGENTA)
                    self.error = "INVALID IP"
                else:
                    log(f"[CLIENT ERROR]: {e}", MAGENTA)
                    self.error = "NETWORK NOT AVIABLE"
                self.online = False
                self.client = None

    def send_to_all(self, data):
        try:
            data_str = str(data)
            for client in self.clients:
                    client.send(data_str.encode("utf-8"))
        
        except Exception as e:
            self.clients.remove(client)
            log(f"[ERROR en enviar_a_todos]: {e}", RED)

    def update_clients(self):
        try:
            while self.is_running:
                
                for client in self.clients:
                    if not self.client_conected(client):
                        client.close()
                        self.clients.remove(client)
                time.sleep(0.1)
                
        except Exception as e:
            self.clients.remove(client)
            log(f"[ERROR actualizar_clientes]: {e}", RED)

    @staticmethod
    def client_conected(client):
        try:
            client.send(" ".encode("utf-8"))
            time.sleep(1)
        except Exception as e:
            log(f"[ERROR client_conected] {e}",RED)
            return False
        return True

    def stop_server(self):
        for client in self.clients:
            client.close()
        if self.server is not None:
            self.server.close()
            self.server = None

    def stop_client(self):
        if self.client is not None:
            self.client.close()
            self.client = None
        
    # COMINICATION
    def recive_data(self):
        
        while self.is_running:
            data_to_recv = self.pipe.recv()
            
            if self.mode == "master":
                if 'tc' in data_to_recv:
                    self.timecode = data_to_recv["tc"]
                    self.send_to_all(self.timecode)
                
            if 'host' in data_to_recv:
                self.host = data_to_recv["host"]   

            if 'port' in data_to_recv:
                self.port = data_to_recv["port"]               

            if 'network_is_on' in data_to_recv:
                self.network_is_on = data_to_recv["network_is_on"]
                  
                if not self.network_is_on and self.mode == "master":
                    self.stop_server()
                
                elif self.mode == "slave":
                    self.stop_client()
                
            if 'mode' in data_to_recv:
                self.mode = data_to_recv["mode"]
            
            if 'is_running' in data_to_recv:
                self.close()   
            
            self.direccion = f"{self.host}:{self.port}"
            self.server_address = (self.host, self.port)

    def send_data(self):
        self.last_online = self.online
        self.last_error = self.error
        self.last_clients = self.clients
        self.last_timecode_recv = self.timecode_recv
        
        while self.is_running:
            data_to_send = {}
            if self.last_online != self.online:
                data_to_send['online'] = self.online
                self.last_online = self.online

            if self.last_error != self.error:
                data_to_send['error'] = self.error
                self.last_error = self.error

            if self.last_clients != self.clients:
                data_to_send['clients'] = self.clients
                self.last_clients = self.clients.copy()

            if self.last_timecode_recv != self.timecode_recv and self.mode == "slave":
                data_to_send['timecode_recv'] = self.timecode_recv
                self.last_timecode_recv = self.timecode_recv
                    
            if data_to_send:
                self.pipe.send(data_to_send)
            time.sleep(0.01)

   # END
    def close(self):
        self.is_running = False
        self.network_is_on = False
        
        self.stop_server()
        self.stop_client()
        
        self.recive_thread.join()
        self.recive_thread.join()
        self.update_clients_thread.join()
        
        proceso_actual = multiprocess.current_process()
        proceso_actual.terminate()        