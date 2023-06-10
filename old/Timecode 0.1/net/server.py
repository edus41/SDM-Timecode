import socketserver
import threading
import time

class MiTcpHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        data=""
        while data !="salir":
            try:
                data=self.request.recv(1024)
                print(data)
                time.sleep(0.1)
            except:
                print("El cliente se desconecto")
                data="salir"
            
class ThreadServer(socketserver.ThreadingMixIn,socketserver.TCPServer):
    pass

def main():
    host="localhost"
    port=9999
    server=ThreadServer((host,port),MiTcpHandler)
    server_thread=threading.Thread(target=server.serve_forever)
    server_thread.start()
    print("server Corriendo")
    
main()
