from multiprocessing import Process
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
import time
from socket import *
from tools import *

##############################################
##----------------- SERVER -----------------##
##############################################

class Network(Process):

    def __init__(self, network_pipe):
        Process.__init__(self)
        
        # privates
        self.pipe = network_pipe
        self.clients_ports = [37020, 37021, 37022, 37023, 37024, 37025, 37026, 37027, 37028, 37029]
        self.last_timecode = 0
        self.server = None
        self.client = None
        
        # to recive
        self.host = "192.168.0.9"
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
        
        # SEND CONFIRMATION
        self.last_online = self.online
        self.last_error = self.error
        self.last_clients = self.clients
        self.last_timecode_recv = self.timecode_recv

    def run(self):
        self.recive_thread = Thread(target = self.recive_data)
        self.recive_thread.start()
        while True:
                while not self.online and self.network_is_on and self.mode == "master":
                    try:
                        if not self.network_is_on:
                                break
                        self.server = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
                        self.server.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
                        self.server.settimeout(0.01)
                        self.server.bind((self.host, self.port))
                        self.send_data()
                        time.sleep(1)
                        self.online = True
                        self.error = None
                        self.send_data()
                        
                        while self.online and self.network_is_on and self.mode == "master":
                            if not self.network_is_on:
                                break
                            if self.last_timecode != self.timecode: 
                                with ThreadPoolExecutor() as executor:
                                    executor.map(self.server_brodcast, self.clients_ports)
                                self.last_timecode = self.timecode
                            time.sleep(0.01)
                        
                        if not self.network_is_on:
                                break    
                    except Exception as e:
                        
                        if "10048" in str(e):
                            log(f"[SERVER ERROR]: Ya Existe Un Servidor Iniciado en: {self.direccion}, Reintentando...", RED)
                            self.error = "NETWORK NOT AVIABLE"
                        elif "11001" in str(e):
                            log(f"[SERVER DISCONECTED]: IP FORMAT INVALID {e}", RED)
                            self.error = "IP FORMAT INVALID"
                        elif "10049" in str(e):
                            log(f"[SERVER DISCONECTED]: INVALID IP {e}", RED)
                            self.error = "INVALID IP"
                        elif "10038" in str(e):
                            log(f"[SERVER DISCONECTED]: Stop Event, {e}", RED)
                            self.error = None
                        else:
                            log(f"[SERVER DISCONECTED]: {e}", RED)
                            self.error = "SERVER ERROR"
                            
                        self.online = False
                        self.server = None
                        self.send_data()
                        time.sleep(1)         
                
                while not self.online and self.network_is_on and self.mode == "slave":
                    self.error = None
                    for port in self.clients_ports:
                        try:
                            if not self.network_is_on:
                                break
                            self.client = socket(AF_INET, SOCK_DGRAM) # UDP
                            self.client.settimeout(0.01)
                            self.client.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
                            self.client.bind((self.host, port))
                            self.send_data()
                            time.sleep(1)
                            self.online = True
                            self.error = None
                            self.send_data()
                            
                            while self.online and self.network_is_on and self.mode == "slave":
                                if not self.network_is_on:
                                    break
                                try:
                                    data, addr = self.client.recvfrom(1024)
                                except timeout:
                                    continue
                                data_str = data.decode("utf-8")
                                self.timecode_recv = float(data_str)
                                self.send_data()
                                #log(self.timecode_recv,YELLOW)
                                
                            if not self.network_is_on:
                                    break
                            
                        except error as e:
                            if "10048" in str(e):
                                log(f"[CLIENT ERROR]: Failed to open connection on port {port} {e}", MAGENTA)
                                self.error = None
                            elif "10054" in str(e):
                                log(f"[CLIENT ERROR]: not server found {e}", MAGENTA)
                                self.error = "NOT SERVER FOUND"
                            elif "11001" in str(e):
                                log(f"[CLIENT ERROR]: INVALID IP FORMAT {e}", MAGENTA)
                                self.error = "INVALID IP FORMAT"
                            elif "10049" in str(e):
                                log(f"[CLIENT ERROR]: INVALID IP {e}", RED)
                                self.error = "INVALID IP"
                            else:
                                log(f"[CLIENT ERROR]: {e}", MAGENTA)
                                self.error = "NETWORK NOT AVIABLE"
                            self.online = False
                            self.client = None
                            self.send_data()
                            time.sleep(1)      
                if self.client is not None:
                    self.client.close()
                    self.client = None  
                    
                if self.server is not None:
                    self.server.close()
                    self.server = None
                                
                if self.online:
                    self.online = False
                    self.error = None
                    self.send_data()
 
                time.sleep(0.1)

    def server_brodcast(self,port):
        try:
            timecode_str = str(self.timecode)
            self.server.sendto(bytes(timecode_str, "utf-8"), ('<broadcast>', port))
        except error as e:
            log(f"[SERVER SEND ERROR ON PORT {port}]: {e}", RED)

    # COMINICATION
    def recive_data(self):
        
        while True:
            data_to_recv = self.pipe.recv()
            
            if self.mode == "master":
                if 'tc' in data_to_recv:
                    self.timecode = data_to_recv["tc"]
                
            if 'host' in data_to_recv:
                self.host = data_to_recv["host"]   

            if 'port' in data_to_recv:
                self.port = data_to_recv["port"]               

            if 'network_is_on' in data_to_recv:
                self.network_is_on = data_to_recv["network_is_on"]   
                
            if 'mode' in data_to_recv:
                self.mode = data_to_recv["mode"]   
            
            self.direccion = f"{self.host}:{self.port}"
            self.server_address = (self.host, self.port)

    def send_data(self):
        data_to_send = {}

        if self.last_online != self.online:
            data_to_send['online'] = self.online
            self.last_online = self.online

        if self.last_error != self.error:
            data_to_send['error'] = self.error
            self.last_error = self.error

        if self.last_clients != self.clients:
            data_to_send['clients'] = self.clients
            self.last_clients = self.clients

        if self.last_timecode_recv != self.timecode_recv and self.mode == "slave":
            data_to_send['timecode_recv'] = self.timecode_recv
            self.last_timecode_recv = self.timecode_recv

        if data_to_send:
            self.pipe.send(data_to_send)
            