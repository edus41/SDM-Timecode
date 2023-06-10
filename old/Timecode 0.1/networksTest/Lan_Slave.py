import socket
import tkinter as tk

class ClientApp:
    def __init__(self):
        self.host = None
        self.port = 12345  # Cambia esto con el puerto del servidor

        self.root = tk.Tk()
        self.root.title("Cliente")
        self.root.geometry("300x100")

        self.host_label = tk.Label(self.root, text="Dirección IP del servidor:")
        self.host_label.pack()

        self.host_entry = tk.Entry(self.root)
        self.host_entry.pack()

        self.connect_button = tk.Button(self.root, text="Conectar", command=self.connect_to_server)
        self.connect_button.pack()

        self.status_label = tk.Label(self.root, text="")
        self.status_label.pack()

        self.root.protocol("WM_DELETE_WINDOW", self.close_window)

        self.running = False

    def connect_to_server(self):
        self.host = self.host_entry.get()
        if self.host:
            try:
                self.status_label.config(text="Conectando al servidor...")
                self.root.update()

                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((self.host, self.port))

                self.status_label.config(text="Conectado al servidor.")
                self.root.update()

                self.running = True

                while self.running:
                    client_socket.send('get'.encode('utf-8'))
                    data = client_socket.recv(1024).decode('utf-8')
                    print(f"Recibido: {data}")

            except socket.error as e:
                self.status_label.config(text=f"No se pudo conectar al servidor: {e}")
                self.root.update()

            finally:
                client_socket.close()
        else:
            self.status_label.config(text="Por favor, ingresa la dirección IP del servidor.")
            self.root.update()

    def close_window(self):
        self.running = False
        self.root.destroy()

    def run(self):
        self.root.mainloop()

client_app = ClientApp()
client_app.run()
