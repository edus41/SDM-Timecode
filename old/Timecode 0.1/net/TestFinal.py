from network3 import *
import time

sv = Servidor()
sv.start()
time.sleep(2)

i=0
while i<5:
    sv.send_menssage_to_all(f"{i}")
    i+=1
    time.sleep(0.5)

time.sleep(5)
sv.stop()

time.sleep(5)
sv.start()
time.sleep(2)

i=0
while i<5:
    sv.send_menssage_to_all(f"{i}")
    i+=1
    time.sleep(0.5)

time.sleep(5)
sv.stop()
""" sv = Servidor()
cli = Cliente()

cli.start()
time.sleep(2)
sv.start()
time.sleep(2)

print("mandando mensaje")

i=0
while i<5:
    sv.send_menssage_to_all(f"{i}")
    i+=1
    time.sleep(0.5)

time.sleep(2)
sv.stop()
time.sleep(10)
cli.stop() """