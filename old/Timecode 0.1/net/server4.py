import time
from socket import *
from threading import Thread, current_thread,Lock
from logs_tools import *

host="127.0.0.1"
port = 12345
direccion = f"{host}:{port}"
online = False
connections = []
connections_lock = Lock()

def receiver(conexion,address):
    while conexion in connections:
        try:
            recData = conexion.recv(1024).decode()
            if not recData:
                log(f"[BAD DATA RECIVED] disconecting client {address}", RED)
                with connections_lock:
                    connections.remove(conexion)
                break
            print("Cliente Dice:", recData)
        except Exception as e:
            log(f"[CLIENTE DESCONECTADO]: el cliente ya no esta disponible para recibir", RED)
            with connections_lock:
                connections.remove(conexion)
            break
        
""" def sender(conexion):
    global online
    while online:
        data = "Hola soy server"
        try:
            conexion.send(bytes(data, "utf-8"))
            time.sleep(0.5)
        except Exception as e:
            log(f"[CLIENTE DESCONECTADO]: el cliente ya no esta disponible para enviar", RED)
            online = False
            break """

def all_sender():
    global online
    while online:
        with connections_lock:
            clients = list(connections)  # Crear una copia de la lista para evitar problemas de iteración y modificación simultánea
        for client in clients:
            with connections_lock:
                lens=len(connections)
                print(f"conexiones: {lens}")
            data = "Hola soy server"
            try:
                client.send(bytes(data, "utf-8"))
                time.sleep(0.5)
            except Exception as e:
                log("[CLIENTE DESCONECTADO]: el cliente ya no esta disponible para enviar", RED)
                with connections_lock:
                    connections.remove(client)


    

while not online:
    try:
        s = socket(AF_INET, SOCK_STREAM)
        s.bind((host, port))
        log(f"[SERVER START ON]: {direccion}", GREEN)
        s.listen(5)
        log(f"[SERVER LISTENING ON]: {direccion}", GREEN)
        online = True
        
        while online:
            connection, address = s.accept()
            log(f"[CLIENTE CONECTADO]: {address}", GREEN)
            with connections_lock:
                connections.append(connection)
            
            #sender_thread: Thread = Thread(target = sender, args=(connection,))
            sender_thread: Thread = Thread(target = all_sender)
            receiver_thread: Thread = Thread(target = receiver, args=(connection,address))
            
            sender_thread.start()
            receiver_thread.start()
            
            sender_thread.join()
            receiver_thread.join()
            
    except KeyboardInterrupt:
        break
    except Exception as e:
        if e.errno == 10048:
            log(f"[SERVER ERROR]: Ya Existe Un Servidor Iniciado en: {direccion}, Reintentando...", RED)
        else:
            log(f"[SERVER ERROR]: Desconosido", RED)
        online = False
        time.sleep(1)


 


