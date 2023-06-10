# from multiprocess import Process, Queue
from threading import Thread, Event
import time
import numpy as np
import soundfile as sf
import sounddevice as sd


class Player:
    def __init__(
        self,
        start_time="00:00:00:00",
        end_time="23:59:59:00",
        fps=30,
        timecode="00:00:00:00",
    ):
        self.audio_is_open = False
        self.audio_devices = self.get_output_devices()
        self.audio_total_duration = 0
        self.audio_data = None
        self.sample_rate = None
        self.stream = None
        self.audio_device = sd.default.device

        self.fps = fps
        self.timecode = timecode

        self.start_time = self.timecode_to_seconds(start_time)
        self.end_time = self.timecode_to_seconds(end_time)
        self.time_now = self.start_time
        self.current_sample = 0

        self.player_stop_event = Event()
        self.mtc_stop_event = Event()
        self.end_event = Event()
        self.mtc_on = True
        self.is_playing = False

        self.player_thread = Thread(
            target=self.play_audio, args=(self.player_stop_event,)
        )
        self.tc_thread = Thread(target=self.play_tc, args=(self.player_stop_event,))
        self.root_thread = Thread(
            target=self.root,
            args=(self.end_event,),
        )
        self.root_thread.start()

    def start(self):
        self.is_playing = True
        self.restart_threads()

    def root(self, root_stop_event):
        self.end_event.clear()
        self.player_stop_event.clear()
        self.mtc_stop_event.clear()

        while not root_stop_event.is_set():
            if self.is_playing:
                self.restart_threads()
                self.is_playing = False

            time.sleep(0.01)

    def restart_threads(self):
        # finish open threads
        if self.player_thread and self.player_thread.is_alive():
            self.player_thread.join()
        if self.tc_thread and self.tc_thread.is_alive():
            self.tc_thread.join()

        # open threads
        if self.audio_data is not None and self.sample_rate is not None:
            self.player_thread = Thread(
                target=self.play_audio, args=(self.player_stop_event,)
            )
            self.player_thread.start()
        else:
            self.tc_thread = Thread(target=self.play_tc, args=(self.player_stop_event,))
            self.tc_thread.start()

        if self.mtc_on:
            self.mtc_thread = Thread(target=self.play_mtc, args=(self.mtc_stop_event,))
            self.mtc_thread.start()

        # reset stop events threads
        self.player_stop_event.clear()
        self.mtc_stop_event.clear()

    def play_tc(self, stop_event):
        time_start = time.time()
        while self.time_now < self.end_time and not stop_event.is_set():
            self.time_now = (time.time() - time_start) + self.start_time
            self.timecode = self.seconds_to_timecode(self.time_now)
            # print("\r", self.timecode, end="")
            time.sleep(1 / self.fps)

    def play_audio(self, stop_event):
        self.stream = sd.OutputStream(
            callback=self.audio_callback,
            channels=self.audio_data.shape[1],
            samplerate=self.sample_rate,
            device=self.audio_device,
        )

        with self.stream and not stop_event.is_set():
            self.current_sample = 0
            while self.current_sample < len(self.audio_data):
                time.sleep(0.1)  # Pequeña pausa para evitar bloquear la CPU

    def audio_callback(self, outdata, ff, time, status):
        if self.current_sample < len(self.audio_data):
            outdata[:ff, :] = np.resize(
                self.audio_data[self.current_sample : self.current_sample + ff, :],
                (ff, 2),
            )
            self.current_sample += ff
            segundo_actual = self.current_sample / self.sample_rate
            self.timecode = self.seconds_to_timecode(segundo_actual)
            print("\r", self.timecode, end="")

    def play_mtc(self, stop_event):
        i = 0
        while self.mtc_on and not stop_event.is_set():
            print("\r", "MTC: ", self.timecode, end="")
            i += 1
            time.sleep(1 / self.fps)

    def open_audio_file(self, audio_file_path):
        audio_data, sample_rate = sf.read(audio_file_path)
        self.audio_total_duration = len(audio_data) / sample_rate
        self.audio_data = audio_data
        self.sample_rate = sample_rate

    def close_audio_file(self):
        self.audio_data = None
        self.sample_rate = None
        self.stream = None

    def get_output_devices(self):
        devices = sd.query_devices()
        output_devices = {}

        for device in devices:
            if (
                device["max_output_channels"] > 0
                and device["hostapi"] == 0
                and device["name"] != "Asignador de sonido Microsoft - Output"
            ):
                index = device["index"]
                name = device["name"]
                output_devices[index] = name

        return output_devices

    def set_output_device(self, device_index):
        self.audio_device = device_index

    def set_fps(self, fps):
        self.fps = fps

    def set_start_time(self, start_time):
        self.start_time = self.timecode_to_seconds(start_time)

    def set_end_time(self, end_time):
        self.end_time = self.timecode_to_seconds(end_time)

    def timecode_to_seconds(self, timecode):
        horas, minutos, segundos, frames = map(int, timecode.split(":"))
        total_seconds = (horas * 3600) + (minutos * 60) + segundos + (frames / self.fps)
        return total_seconds

    def seconds_to_timecode(self, seconds):
        hh = int(seconds / 3600)
        mm = int((seconds % 3600) / 60)
        ss = int(seconds % 60)
        ff = int((seconds * self.fps) % self.fps)
        return f"{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}"

    def stop(self):
        self.player_stop_event.set()
        self.mtc_stop_event.set()

    def end(self):
        print("END")
        self.end_event.set()
        self.stop()


if __name__ == "__main__":
    player = Player()
    # player.open_audio_file("C:\\Users\\Eduardo Rodriguez\\Desktop\\audio.wav")
    # player.set_start_time("00:01:00:00")
    # player.set_end_time("00:01:05:00")
    time.sleep(1)
    print("ready")
    player.start()
    time.sleep(5)
    player.stop()
    player.end()
