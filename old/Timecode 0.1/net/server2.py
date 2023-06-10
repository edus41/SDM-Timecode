import time
from socket import *
from threading import Thread, current_thread

class ChatThread(Thread):
    def __init__(self, con, addr):
        Thread.__init__(self)
        self.con = con
        self.addr = addr

    def run(self):
        name = current_thread().name
        while True:
            if name == "Sender":
                print("New connection:", self.addr)
                data = input("Server: ")
                try:
                    self.con.send(bytes(data, "utf-8"))
                except:
                    print("CONNECTION LOST")
                    break

            elif name == "Receiver":
                try:
                    recData = self.con.recv(1024).decode()
                    if not recData:
                        print("CONNECTION LOST")
                        self.con.close()
                        break
                    print("Client:", recData)
                except:
                    print("CONNECTION LOST")
                    self.con.close()
                    break

def start_server():
    server = socket(AF_INET, SOCK_STREAM)
    server.bind(("127.0.0.1", 15000))
    server.listen(4)
    connections = []
    try:
        while True:
            connection, address = server.accept()
            connections.append(connection)
            sender = ChatThread(connection, address)
            sender.name = "Sender"
            receiver = ChatThread(connection, address)
            receiver.name = "Receiver"
            sender.start()
            receiver.start()
    except KeyboardInterrupt:
        pass
    finally:
        server


# Iniciar el servidor
while True:
    try:
        start_server()
    except KeyboardInterrupt:
        break
    except:
        print("Server disconnected. Reconnecting in 1 second...")
        time.sleep(1)
        continue
