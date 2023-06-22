import socket
import time

ip_address = "127.0.0.1"
port = 6454

timecode_type = 0

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

for i in range(0, 3600):
    ss = int(i / 30)
    hh = int(ss / 3600)
    mm = int((ss % 3600) / 60)
    ff = int(i % 30)

    artnet_packet = bytearray()
    artnet_packet.extend(b"Art-Net\x00")
    artnet_packet.extend(b"\x00\x97")
    artnet_packet.extend(b"\x00\x0e")
    artnet_packet.extend(b"\x00\x00")
    artnet_packet.extend(bytes([ff]))  # Hours
    artnet_packet.extend(bytes([ss]))  # Minutes
    artnet_packet.extend(bytes([mm]))  # Seconds
    artnet_packet.extend(bytes([hh]))  # Frames
    artnet_packet.extend(bytes([timecode_type]))  # Timecode Type
    print(artnet_packet)
    sock.sendto(artnet_packet, (ip_address, port))
    time.sleep(1/30)

sock.close()
