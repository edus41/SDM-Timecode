import socket

ip_address = "127.0.0.1"
port = 6454

# Crear el socket UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((ip_address, port))

while True:
    try:
        data, addr = sock.recvfrom(1024)
        print(data)
        if data.startswith(b"Art-Net") and data[8:18] == b"OpTimeCode":
            timecode = f"{str(data[22]).zfill(2)}:{str(data[23]).zfill(2)}:{str(data[24]).zfill(2)}:{str(data[25]).zfill(2)}"
            print("TC: ",timecode)

    except KeyboardInterrupt:
        sock.close()
        break
