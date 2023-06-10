from network3 import *
import time

cli = Cliente()

cli.start()
time.sleep(20)
cli.stop()