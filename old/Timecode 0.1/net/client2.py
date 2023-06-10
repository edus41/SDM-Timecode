import time
from socket import *
from threading import Thread, current_thread

class ChatThread(Thread):
    def __init__(self, con):
        Thread.__init__(self)
        self.con = con

    def run(self):
        name = current_thread().name
        while True:
            if name == "Sender":
                data = input("Client: ")
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
                    print("Server:", recData)
                except:
                    print("CONNECTION LOST")
                    self.con.close()
                    break

def start_client():
    while True:
        connected = False
        client = socket()
        try:
            while True:
                if not connected:
                    try:
                        client.connect(("127.0.0.1", 15000))
                        print("Connected to server")
                        connected = True
                        break
                    except:
                        pass

                time.sleep(1)

            sender = ChatThread(client)
            sender.name = "Sender"
            receiver = ChatThread(client)
            receiver.name = "Receiver"

            sender.start()
            receiver.start()

            sender.join()
            receiver.join()

            # Si alguno de los hilos termina, significa que se perdió la conexión
            print("Server disconnected")
            client.close()
            connected = False
        except KeyboardInterrupt:
            break
        except:
            if connected:
                print("Server disconnected. Reconnecting...")
            else:
                print("Failed to connect to server. Retrying...")
            time.sleep(1)
            continue

# Iniciar el cliente
if __name__ == "__main__":
    start_client()
