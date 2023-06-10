import multiprocessing
from multiprocessing import Process
import time
from socket import *
from threading import Thread, current_thread,Event
from logs_tools import *

host="127.0.0.1"
port = 12345
direccion = f"{host}:{port}"
connected = False
name=input("Name: ")

def receiver(conexion):
    global connected
    while connected:
        try:
            recData = conexion.recv(1024).decode()
            if not recData:
                log(f"[BAD DATA RECIVED] server disconected", MAGENTA)
                connected = False
                break
            print("Server Dice:", recData)
        except Exception as e:
            connected = False
            log(f"[CONNECTION LOST 3]: {e}", MAGENTA)
            break
        
def sender(conexion):
    global connected
    while connected:
        data = f"Hola soy cliente, {name}"
        try:
            conexion.send(bytes(data, "utf-8"))
            time.sleep(1)
        except Exception as e:
            connected = False
            log(f"[CONNECTION LOST]: No se Puedo Enviar el Mensaje", MAGENTA)
            break


               
while not connected:
    try:
        client = socket()
        log(f"[CLIENT START]", CYAN)
        client.connect((host, port))    
        log(f"[CLIENT CONECTED]: {direccion}", CYAN)
        connected = True
        
        while connected:
            
            receiver_thread: Thread = Thread(target = receiver, args=(client,))
            sender_thread: Thread = Thread(target = sender, args=(client,))
            
            receiver_thread.start()
            sender_thread.start()
            sender_thread.join()
            receiver_thread.join()

            log(f"[SERVER UNAVAILABLE]: {direccion}", MAGENTA)
            client.close()
            connected = False
            
    except KeyboardInterrupt:
        break
    
    except Exception as e:
        if e.errno == 10061:
            log(f"[SERVER ERROR]: Ningun Servidor Disponible En: {direccion}, Reintentando...", MAGENTA)
        else:
            log(f"[SERVER ERROR]: {e}", MAGENTA)
        connected = False
        time.sleep(1)
    