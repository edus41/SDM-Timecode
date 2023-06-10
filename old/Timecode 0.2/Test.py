from multiprocess import Process, Queue
from Server_Prosess import Server
import time


class Backend(Process):
    def __init__(self):
        super().__init__()
        self.message_server = Queue()
        self.status_server = Queue()
        self.server = Server(message=self.message_server, status=self.status_server)

    def run(self):
        i = 0
        while True:
            time.sleep(2)
            self.message_server.put(i)
            print(f"SERVER: {self.status_server.get()}")
            i += 1
            time.sleep(0.5)

    def send_to_clients(self, message):
        self.message_server.put(message)

    def stop_server(self):
        self.server.stop()

    def start_server(self):
        self.server.iniciar()


if __name__ == "__main__":
    back = Backend()
    back.start()
    back.start_server()
    # time.sleep(5)
    # back.stop_server()
    # back.terminate()


"""def senders():
    while is_playing:
        if ltc_on:
            print("playing LTC")
            play_ltc()
        if mtc_on:
            print("playing MTC")
            play_mtc()
        if server_on:
            print("playing SERVER")
            server.send(timecode)
        time.sleep(1 / fps)


def play_ltc():
    audiodata = LTC.make_ltc_audio(self.ltc_tc)
    if self.audio_device.stream:
        self.audio_device.play(audiodata)


def play_mtc():
    self.mtc_tc = add_tcs(self.mtc_offset, self.tc, self.mtc_fps)
    if self.midi_device.midi_out:
        self.midi_device.sendMTC(self.mtc_tc)"""
