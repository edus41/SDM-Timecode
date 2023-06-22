from multiprocessing import Process
from socket import *
import time
from threading import Thread
import inspect
from tools import *
import time

class Network(Process):
    
    def __init__(self, network_pipe):
        Process.__init__(self)
        
        self.is_running = True
        self.pipe = network_pipe
        
        self.client_address = "127.0.0.1"
        self.port = 6454
        
        self.timecode = 0
        self.last_frames = 0
        self.frames=0
        self.timecode_recv = 0
        self.timecode_type = 0
        self.fps = 30
        
        self.mode = "master"
        self.network_is_on = False
        self.online = False
        self.error = None
        
        self.clients = []
        self.update_clients_running = None

    def run(self):
        self.recive_thread = Thread(target = self.recive_data)
        self.recive_thread.start()
        
        self.send_thread = Thread(target = self.send_data)
        self.send_thread.start()
        
        while self.is_running:
            try:
                while not self.online and self.network_is_on and self.is_running:
                    
                    self.sock = socket(AF_INET, SOCK_DGRAM)
                    if self.mode == "slave":
                        self.sock.bind((self.client_address, self.port))
                        self.sock.settimeout(1)
                    
                    self.online = True
                    self.error = None
                    
                    while self.online and self.network_is_on and self.is_running:
                        self.frames = int(self.timecode*self.fps)
                        if self.mode == "master" and self.last_frames != self.frames:
                            self.send_art_net_timecode()
                            self.last_frames = self.frames
                            
                        elif self.mode == "slave":
                            self.recv_art_net_timecode()
                    
                    if self.sock is not None:
                        self.close()  

                time.sleep(0.1)
            
            except Exception as e:
                error_message = str(e)
                if "10048" in error_message:
                    log(f"[NETWORK ERROR]: Ya Existe Un Servidor Iniciado en: {self.client_address}:{self.port}, Reintentando...",WARNING)
                    self.error = "NETWORK NOT AVAILABLE"
                elif "11001" in error_message:
                    log(f"[NETWORK ERROR]: INVALID IP / PORT VALUE {error_message}",WARNING)
                    self.error = "INVALID IP / PORT VALUE"
                elif "10049" in error_message:
                    log(f"[NETWORK ERROR]: INVALID IP {error_message}",WARNING)
                    self.error = "INVALID IP"
                elif "10038" in error_message:
                    log(f"[NETWORK DISCONNECTED]: Stop Event {error_message}")
                    self.error = None
                elif "0-65535" in error_message:
                    log(f"[NETWORK ERROR]: PORT MUST BE 0-65535 {error_message}",WARNING)
                    self.error = "PORT MUST BE 0-65535"
                elif "interpreted" in error_message:
                    log(f"[NETWORK ERROR]: INVALID IP / PORT VALUE {e}")
                    self.error = "INVALID IP / PORT VALUE"
                else:
                    log(f"[NETWORK ERROR {inspect.currentframe().f_code.co_name}]: {e}")
                    self.error = "NETWORK ERROR"
                    
                self.online = False
                self.error = None
                time.sleep(1)          

    def send_art_net_timecode(self):
            hh = int(self.timecode / 3600)
            mm = int((self.timecode % 3600) / 60)
            ss = int(self.timecode % 60)
            ff = int((self.timecode * 30) % 30)

            artnet_packet = bytearray()
            artnet_packet.extend(b"Art-Net\x00")
            artnet_packet.extend(b"\x00\x97")
            artnet_packet.extend(b"\x00\x0e")
            artnet_packet.extend(b"\x00\x00")
            artnet_packet.extend(bytes([ff]))  # Hours
            artnet_packet.extend(bytes([ss]))  # Minutes
            artnet_packet.extend(bytes([mm]))  # Seconds
            artnet_packet.extend(bytes([hh]))  # Frames
            artnet_packet.extend(bytes([self.timecode_type]))  # Timecode Type

            for client in self.clients:
                try:
                    self.sock.sendto(artnet_packet, (client, self.port))
                except Exception as e:
                    log(f"send tc to client error: {e}")

    def recv_art_net_timecode(self):
            try:
                data, addr = self.sock.recvfrom(1024)
                    
                if data.startswith(b"Art-Net") and data[8:18] == b"OpTimeCode":
                    recv_timecode = f"{data[21]}:{data[20]}:{data[19]}:{data[18]}"
                    self.timecode_recv = tc_to_secs(recv_timecode,self.fps)
                    
            except timeout:
                pass
            
            except Exception as e:
                log(f"[NETWORK ERROR {inspect.currentframe().f_code.co_name}]: {e}")
                self.error = "NETWORK ERROR"
        
    # COMINICATION
    def recive_data(self):
        try:
            while self.is_running:
                data_to_recv = self.pipe.recv()

                if 'tc' in data_to_recv:
                    self.timecode = data_to_recv["tc"]
                
                if 'host' in data_to_recv:
                    self.client_address = data_to_recv["host"] 

                if 'network_is_on' in data_to_recv:
                    self.network_is_on = data_to_recv["network_is_on"]
                    
                if 'mode' in data_to_recv:
                    self.mode = data_to_recv["mode"]
                    
                if 'clients' in data_to_recv:
                    self.clients = data_to_recv["clients"]

                if 'is_running' in data_to_recv:
                    self.stop()   
                
        except Exception as e:
            log(f"[ERROR NET {inspect.currentframe().f_code.co_name}]: {e}")

    def send_data(self):
        try:
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

                if self.last_timecode_recv != self.timecode_recv:
                    data_to_send['timecode_recv'] = self.timecode_recv
                    self.last_timecode_recv = self.timecode_recv

                if data_to_send:
                    self.pipe.send(data_to_send)
                time.sleep(0.01)
                
        except Exception as e:
            log(f"[ERROR NET {inspect.currentframe().f_code.co_name}]: {e}")

    def close(self):
        self.online = False
        self.error = None
        if self.sock is not None:
            self.sock.close()
            self.sock = None
    
    def stop(self):
        self.is_running = False
        self.update_clients_running = False
        self.close()