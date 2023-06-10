import socket

def main():
    
    msj=""
    print("Cliente 1.0")
    host,port="localhost",9999
    sock=socket.socket()
    sock.connect((host,port))
    while msj != "salir":
        print ("Ingrese un mensaje o salir para terminar")
        msj = input("Usted dice:")
        try:
            sock.send(msj)
        except:
            print("no se mando el mensaje")
            msj="salir"
        
    sock.close()

main()