import multiprocessing
from multiprocessing import Process
import time
from socket import *
from threading import Thread, current_thread, Event
from logs_tools import *


class Client:
    def __init__(self, host="127.0.0.1", port=12345):
        self.host = host
        self.port = port
        self.direccion = f"{host}:{port}"
        self.client = None
        self.connected = False
        self.ultimo_mensaje = ""
        self.stop_event = Event()

    def start(self):
        self.stop_event.clear()
        self.client_thread: Thread = Thread(target=self._conect)
        self.client_thread.start()

    def _conect(self):
        while not self.connected:
            if self.stop_event.is_set():
                break
            try:
                self.client = socket()
                log(f"[CLIENT START]: {self.direccion}", CYAN)
                self.client.connect((self.host, self.port))
                log(f"[CLIENT CONECTED]: {self.direccion}", CYAN)
                self.connected = True

                while self.connected:
                    receiver_thread: Thread = Thread(
                        target=self._receiver, args=(self.client,)
                    )
                    receiver_thread.start()
                    log(f"[LISTENING...]: {self.direccion}", CYAN)

                    receiver_thread.join()

                    log(f"[SERVER UNAVAILABLE]: {self.direccion}", MAGENTA)
                    self.client.close()
                    self.connected = False
                    self.client = None

            except Exception as e:
                # if e.errno == 10061:
                log(
                    f"[ERROR]: Ningun Servidor Disponible En: {self.direccion}, Reintentando...",
                    MAGENTA,
                )
                # else:
                # log(f"[CLIENT ERROR]: {e}", MAGENTA)
                self.connected = False
                self.client = None
                time.sleep(1)

    def _receiver(self, conexion):
        while self.connected:
            if self.stop_event.is_set():
                conexion.close()
                break
            try:
                self.ultimo_mensaje = conexion.recv(1024).decode()
                print(self.ultimo_mensaje)
                if not self.ultimo_mensaje:
                    log(f"[BAD DATA RECIVED] server disconected", MAGENTA)
                    self.connected = False
                    self.client = None
                    break
                # log(f"Server Dice: {self.ultimo_mensaje}",YELLOW)
            except Exception as e:
                self.connected = False
                self.client = None
                log(f"[CONNECTION LOST 3]: {e}", MAGENTA)
                break

    def stop(self):
        self.connected = False
        self.stop_event.set()
        if self.client:
            self.client.close()
            self.client = None
        log(f"[CLIENT DICONECTED]: Stop Event", MAGENTA)


cliente = Client()
cliente.start()
