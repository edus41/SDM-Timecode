from PyQt5 import uic, QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from socket import *
import sys
from logs_tools import *
import time
import ltc_generator as LTC
from py_audio_class import AudioDevice
from py_midi_class import MidiDevice
import time
import numpy as np
import soundfile as sf
import sounddevice as sd
import pyaudio


class WorkerGUI(QRunnable):
    def __init__(self, InFunc):
        super(WorkerGUI, self).__init__()
        self.Func = InFunc

    @pyqtSlot()
    def run(self):
        self.Func()


class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()
        uic.loadUi("gui.ui", self)
        self.setWindowTitle("SDM Timecode")
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        # --------------------- FUNCTION ASSING--------------------------
        # WINDOW ASSING
        self.app_mini_button.clicked.connect(self.showMinimized)
        self.app_close_button.clicked.connect(self.close_app)
        self.tc_label.mouseMoveEvent = self.mouseMoveWindow

        # NETWORK AND MODE ASSING
        # self.master_button.clicked.connect(self.set_master_mode)
        # self.slave_button.clicked.connect(self.set_slave_mode)
        # self.connect_button.clicked.connect(self.set_network)

        # CONTROL BUTTONS ASSING
        self.play_button.clicked.connect(self.play_pause)
        # self.stop_button.clicked.connect(self.stop)
        # self.clock_button.clicked.connect(self.tc_clock)
        # self.forward_button.clicked.connect(self.forward)
        # self.backward_button.clicked.connect(self.backward)
        # self.pin_button.clicked.connect(self.always_on_top)
        # self.lock_button.clicked.connect(self.lock)

        # CONTROL BUTTONS ASSING
        # self.audio_open_button.clicked.connect(self.opne_audio)
        # self.audio_close_button.clicked.connect(self.close_audio)
        # self.audio_slider.valueChanged.connect(self.set_gain)
        # self.audio_output_combo_box.currentIndexChanged.connect(self.set_audio_device)

        # LTC ASSING
        # self.ltc_switch.stateChanged.connect(self.set_ltc_state)
        # self.ltc_offset_button.clicked.connect(self.set_ltc_offset)
        # self.ltc_output_combo_box.currentIndexChanged.connect(self.set_ltc_output)
        # self.ltc_fps_combo_box.currentIndexChanged.connect(self.set_ltc_fps)

        # MTC ASSING
        # self.mtc_switch.stateChanged.connect(self.set_mtc_state)
        # self.mtc_offset_button.clicked.connect(self.set_mtc_offset)
        # self.mtc_output_combo_box.currentIndexChanged.connect(self.set_mtc_output)
        # self.mtc_fps_combo_box.currentIndexChanged.connect(self.set_mtc_fps)

        self.WrkrGUI = WorkerGUI(self.player)

        self.show()

        self.CountThis = False
        self.StartThis = True
        self.RunThis = True

        self.audio_is_open = False
        self.audio_total_duration = 0
        self.audio_data = None
        self.sample_rate = None
        self.stream = None

        self.timecode = "00:00:00:00"
        self.start_time = "00:00:00:00"
        self.end_time = "23:59:59:00"
        self.time_now = self.start_time
        self.current_sample = 0

        self.ltc_audio_device = AudioDevice()
        self.ltc_audio_device.set_output_device(7)
        self.midi_device = MidiDevice()
        self.open_audio_file("C:\\Users\\Eduardo Rodriguez\\Desktop\\audio.wav")

        # BUTTONS / NETWORK / MODE
        self.mode = "master"
        self.network_status = False
        self.is_playing = False
        self.is_pin = False
        self.is_lock = False
        self.host = "127.0.0.1"
        self.port = 12345
        self.tc = "00:00:00:00"
        self.audio_file_name = "OPEN AN AUDIO FILE"
        self.audio_devices = None
        self.midi_devices = None

        # LTC
        self.ltc_fps = 24
        self.ltc_switch_state = True
        self.ltc_offset = "00:00:00:00"
        self.ltc_tc = "00:00:00:00"

        # MTC
        self.mtc_fps = 24
        self.mtc_switch_state = True
        self.mtc_offset = "00:00:00:00"
        self.mtc_tc = "00:00:00:00"
        self.mtc_output_devices = None

        # WIDGETS INIT
        self.users_icon_label.setVisible(False)
        self.users_label.setVisible(False)
        self.slave_button.setChecked(False)
        self.master_button.setChecked(True)

    # ----------------------MAIN FUNCTIONS-----------------------------

    def mousePressEvent(self, event):  # OK
        self.oldPosition = event.globalPos()

    def mouseMoveWindow(self, event):  # OK
        if not self.isMaximized():
            delta = QtCore.QPoint(event.globalPos() - self.oldPosition)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPosition = event.globalPos()

    def close_app(self):  ##EMPTY
        self.close()

    # --------------------------EXEC----------------------------

    def play_pause(self):
        self.CountThis = not self.CountThis
        if self.CountThis and self.StartThis:
            self.StartThis = False
            self.threadpool = QThreadPool()
            self.threadpool.start(self.WrkrGUI)

    def player(self):
        while self.RunThis:
            if self.sample_rate != None:
                self.play_audio()
            else:
                self.play_tc()
            time.sleep(0.1)

    def play_ltc(self):
        if self.ltc_switch_state:
            audiodata = LTC.make_ltc_audio(self.timecode)
            self.ltc_audio_device.play(audiodata)

    def play_mtc(self):
        if self.mtc_switch_state:
            self.midi_device.sendMTC(self.timecode)

    def play_tc(self):
        self.time_start = time.time()
        while self.CountThis:
            self.time_now = time.time() - self.time_start
            self.timecode = self.seconds_to_timecode(self.time_now, 25)
            self.tc_label.setText(self.timecode)
            self.play_ltc()
            self.play_mtc()
            time.sleep(1 / 25)
        self.time_start = time.time()

    def play_audio(self):
        p = pyaudio.PyAudio()
        self.stream = p.open(
            format=pyaudio.paFloat32,
            channels=self.audio_data.shape[1],
            rate=self.sample_rate,
            output=True,
            stream_callback=self.audio_callback,
        )

        self.current_sample = 0
        self.CountThis = True
        self.stream.start_stream()

        while self.current_sample < len(self.audio_data) and self.CountThis:
            time.sleep(0.1)  # Pequeña pausa para evitar bloquear la CPU

        self.stream.stop_stream()
        self.stream.close()
        p.terminate()

    def audio_callback(self, in_data, frame_count, time_info, status):
        if self.current_sample < len(self.audio_data):
            audio_chunk = np.resize(
                self.audio_data[
                    self.current_sample : self.current_sample + frame_count, :
                ],
                (frame_count, 2),
            ).astype(np.float32)

            self.current_sample += frame_count
            segundo_actual = self.current_sample / self.sample_rate
            self.timecode = self.seconds_to_timecode(segundo_actual, 25)
            self.tc_label.setText(self.timecode)
            self.play_ltc()
            self.play_mtc()

            return (audio_chunk.tobytes(), pyaudio.paContinue)
        else:
            return (None, pyaudio.paComplete)

    def open_audio_file(self, audio_file_path):
        audio_data, sample_rate = sf.read(audio_file_path)
        self.audio_total_duration = len(audio_data) / sample_rate
        self.audio_data = audio_data
        self.sample_rate = sample_rate

    def close_audio_file(self):
        self.audio_data = None
        self.sample_rate = None
        self.stream = None

    def timecode_to_seconds(self, timecode, fps):
        horas, minutos, segundos, frames = map(int, timecode.split(":"))
        total_seconds = (horas * 3600) + (minutos * 60) + segundos + (frames / fps)
        return total_seconds

    def seconds_to_timecode(self, seconds, fps):
        hh = int(seconds / 3600)
        mm = int((seconds % 3600) / 60)
        ss = int(seconds % 60)
        ff = int((seconds * fps) % fps)
        return f"{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}"


if __name__ == "__main__":
    mainApp = QApplication(sys.argv)
    app = UI()
    mainApp.exec_()
