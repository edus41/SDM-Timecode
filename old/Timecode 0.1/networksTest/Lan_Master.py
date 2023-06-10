import socket
import threading
import tkinter as tk

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.clients = []
        self.variable = 0
        self.variable_lock = threading.Lock()

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)

    def start(self):
        print(f"Servidor iniciado en {self.host}:{self.port}")
        self.accept_connections()

    def accept_connections(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"Nueva conexión de {client_address[0]}:{client_address[1]}")
            self.clients.append(client_socket)
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        while True:
            try:
                data = client_socket.recv(1024).decode('utf-8')
                if data == 'get':
                    with self.variable_lock:
                        client_socket.send(str(self.variable).encode('utf-8'))
                elif data.startswith('set'):
                    _, value = data.split(':')
                    with self.variable_lock:
                        self.variable = int(value)
                        self.broadcast(str(self.variable).encode('utf-8'))
            except ConnectionResetError:
                self.clients.remove(client_socket)
                break

    def broadcast(self, message):
        for client_socket in self.clients:
            try:
                client_socket.send(message)
            except socket.error:
                self.clients.remove(client_socket)

class App:
    def __init__(self):
        self.server = None
        self.root = tk.Tk()
        self.root.title("Servidor")
        self.root.geometry("200x100")

        self.label = tk.Label(self.root, text="Variable: 0")
        self.label.pack()

        self.start_button = tk.Button(self.root, text="Iniciar", command=self.start_server)
        self.start_button.pack()

    def start_server(self):
        self.server = Server('127.0.0.1', 12345)
        threading.Thread(target=self.server.start).start()
        self.start_button.config(state=tk.DISABLED)

        self.update_variable()

    def update_variable(self):
        with self.server.variable_lock:
            self.label.config(text=f"Variable: {self.server.variable}")
        self.root.after(100, self.update_variable)

    def close_window(self):
        self.running = False
        self.root.destroy()
        
    def run(self):
        self.root.mainloop()

app = App()
app.run()
