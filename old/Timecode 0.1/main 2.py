from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5 import uic, QtCore
from PyQt5.QtCore import Qt

import sys
from timecode import Timecode
import datetime
import time
import re
from colors import *
import ltc_generator as LTC
from timecode_tools import *
from py_audio_class import AudioDevice
from py_midi_class import MidiDevice
from client_class import Client
from server_class import Server

from icons_path import *


class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()
        uic.loadUi("gui.ui", self)
        self.setWindowTitle("SDM Timecode")
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)

        # ----------------------------------------------------------------

        self.tc_thread = TC_Thread(self)
        self.tc_thread.tc_data.connect(self.get_tc_data)
        self.tc_thread.ltc_data.connect(self.get_ltc_data)
        self.tc_thread.mtc_data.connect(self.get_mtc_data)

        # --------------------- FUNCTION ASSING--------------------------
        # WINDOW ASSING
        self.app_mini_button.clicked.connect(self.showMinimized)
        self.app_close_button.clicked.connect(self.close_app)
        self.tc_label.mouseMoveEvent = self.mouseMoveWindow

        # NETWORK AND MODE ASSING
        self.master_button.clicked.connect(self.set_master_mode)
        self.slave_button.clicked.connect(self.set_slave_mode)
        self.connect_button.clicked.connect(self.set_network)
        self.reload_button.clicked.connect(self.set_ip)

        # CONTROL BUTTONS ASSING
        self.play_button.clicked.connect(self.play_pause)
        self.stop_button.clicked.connect(self.stop)
        self.clock_button.clicked.connect(self.tc_clock)
        self.forward_button.clicked.connect(self.forward)
        self.backward_button.clicked.connect(self.backward)
        self.pin_button.clicked.connect(self.always_on_top)
        self.lock_button.clicked.connect(self.lock)

        # CONTROL BUTTONS ASSING
        self.audio_open_button.clicked.connect(self.opne_audio)
        self.audio_close_button.clicked.connect(self.close_audio)
        self.audio_slider.valueChanged.connect(self.set_gain)
        self.audio_output_combo_box.currentIndexChanged.connect(self.set_audio_device)

        # LTC ASSING
        self.ltc_switch.stateChanged.connect(self.set_ltc_state)
        self.ltc_offset_button.clicked.connect(self.set_ltc_offset)
        self.ltc_output_combo_box.currentIndexChanged.connect(self.set_ltc_output)
        self.ltc_fps_combo_box.currentIndexChanged.connect(self.set_ltc_fps)

        # MTC ASSING
        self.mtc_switch.stateChanged.connect(self.set_mtc_state)
        self.mtc_offset_button.clicked.connect(self.set_mtc_offset)
        self.mtc_output_combo_box.currentIndexChanged.connect(self.set_mtc_output)
        self.mtc_fps_combo_box.currentIndexChanged.connect(self.set_mtc_fps)

        self.set_init_state()
        self.show()

    # ----------------------MAIN FUNCTIONS-----------------------------

    def mousePressEvent(self, event):  # OK
        self.oldPosition = event.globalPos()

    def mouseMoveWindow(self, event):  # OK
        if not self.isMaximized():
            delta = QtCore.QPoint(event.globalPos() - self.oldPosition)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPosition = event.globalPos()

    def set_init_state(self):  # EMPTY
        # BUTTONS / NETWORK / MODE
        self.mode = "master"
        self.network_status = False
        self.is_playing = False
        self.is_pin = False
        self.is_lock = False
        self.current_ip = "192.168.000.001"
        self.tc = "00:00:00:00"
        self.audio_file_name = "OPEN AN AUDIO FILE"
        self.audio_devices = None
        self.midi_devices = None

        # LTC
        self.ltc_fps = 24
        self.ltc_switch_state = False
        self.ltc_offset = "00:00:00:00"
        self.ltc_tc = "00:00:00:00"

        # MTC
        self.mtc_fps = 24
        self.mtc_switch_state = False
        self.mtc_offset = "00:00:00:00"
        self.mtc_tc = "00:00:00:00"
        self.mtc_output_devices = None

        # WIDGETS INIT

        self.slave_button.setChecked(False)
        self.master_button.setChecked(True)

        # DEVICES INIT
        self.update_devices_lists()

    def close_app(self):  ##EMPTY
        self.close()

    # ------------------NETWORK AND MODE FUNCTIONS---------------------

    def set_ip(self):  # NO VINCULADA
        self.ip = f"{self.ip_1.text()}.{self.ip_2.text()}.{self.ip_3.text()}.{self.ip_4.text()}"
        ip_valida = (
            re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", self.ip) is not None
        )

    def set_network(self):  # EMPTY
        pass

    def set_master_mode(self):  # NO VINCULADA
        self.master_button.setChecked(True)
        self.slave_button.setChecked(False)

        if self.mode == "master":
            return

        self.mode = "master"
        self.tc = "00:00:00:00"
        if self.is_playing:
            self.stop()
        self.network_status = False

        self.play_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.clock_button.setEnabled(True)
        self.forward_button.setEnabled(True)
        self.backward_button.setEnabled(True)
        self.audio_open_button.setEnabled(True)
        self.audio_close_button.setEnabled(True)
        self.audio_slider.setEnabled(True)
        self.audio_output_combo_box.setEnabled(True)
        self.audio_label.setText("Open An Audio File")

    def set_slave_mode(self):  # NO VINCULADA
        self.master_button.setChecked(False)
        self.slave_button.setChecked(True)

        if self.mode == "slave":
            return

        self.mode = "slave"
        self.tc = "00:00:00:00"

        if self.is_playing:
            self.stop()

        self.network_status = False

        self.play_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.clock_button.setEnabled(False)
        self.forward_button.setEnabled(False)
        self.backward_button.setEnabled(False)
        self.audio_open_button.setEnabled(False)
        self.audio_close_button.setEnabled(False)
        self.audio_slider.setEnabled(False)
        self.audio_output_combo_box.setEnabled(False)
        self.audio_label.setText("Audio Player Is Disable In Slave Mode")

    def update_devices_lists(self):  # TEST
        self.start_tc_thread()

        self.tc_thread.get_audio_devices()
        self.tc_thread.get_midi_devices()

        self.audio_devices = self.tc_thread.audio_devices
        self.midi_devices = self.tc_thread.midi_devices

        self.audio_output_combo_box.clear()
        self.audio_output_combo_box.addItems(list(self.audio_devices.values()))
        self.ltc_output_combo_box.clear()
        self.ltc_output_combo_box.addItems(list(self.audio_devices.values()))
        self.mtc_output_combo_box.clear()
        self.mtc_output_combo_box.addItems(list(self.midi_devices.values()))

        self.stop_tc_thread()

    # ---------------------TC_THREAD FUNCTIONS-------------------------

    def start_tc_thread(self):  # TEST
        self.tc_thread.init()
        self.tc_thread.start()

    def stop_tc_thread(self):  # TEST
        self.tc_thread.stop()

    def get_tc_data(self, tc):  # TEST
        self.tc_label.setText(tc)

    def get_ltc_data(self, tc):  # TEST
        if self.ltc_switch_state:
            self.ltc_tc_label.setText(tc)

    def get_mtc_data(self, tc):  # TEST
        if self.mtc_switch_state:
            self.mtc_tc_label.setText(tc)

    # ----------------------BUTTONS FUNCTIONS--------------------------

    def play_pause(self):  # TEST
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.start_tc_thread()
        else:
            self.stop_tc_thread()

    def stop(self):  # TEST
        self.is_playing = False
        self.play_button.setChecked(False)
        self.stop_tc_thread()
        self.tc = "00:00:00:00"
        self.tc_label.setText(self.tc)
        self.ltc_tc_label.setText(add_tcs(self.tc, self.ltc_offset, 24))
        self.mtc_tc_label.setText(add_tcs(self.tc, self.mtc_offset, 24))

    def forward(self):  # TEST
        limit = Timecode(24, "23:49:59:00")
        tc = Timecode(24, self.tc)

        if self.tc > limit:
            tc = Timecode(24, f"23:59:59:{24-1}")
        else:
            for i in range(10 * 24):
                tc.next()

        self.tc = str(tc)
        self.tc_label.setText(str(tc))
        self.tc_thread.update_tc(tc)
        self.ltc_tc_label.setText(add_tcs(self.tc, self.ltc_offset, 24))
        self.mtc_tc_label.setText(add_tcs(self.tc, self.mtc_offset, 24))

    def backward(self):  # TEST
        limit = Timecode(24, "00:00:10:00")
        tc = Timecode(24, self.tc)

        if self.tc < limit:
            tc = Timecode(24, "00:00:00:00")
        else:
            for i in range(10 * 24):
                tc.back()

        self.tc = str(tc)
        self.tc_label.setText(str(tc))
        self.tc_thread.update_tc(tc)
        self.ltc_tc_label.setText(add_tcs(self.tc, self.ltc_offset, 24))
        self.mtc_tc_label.setText(add_tcs(self.tc, self.mtc_offset, 24))

    def tc_clock(self):  # TEST
        current_time = datetime.datetime.now()
        current_time_str = current_time.strftime("%H:%M:%S:%f")[:-3]
        tc = Timecode(24, start_timecode=current_time_str)

        self.tc = str(tc)
        self.tc_label.setText(str(tc))
        self.tc_thread.update_tc(tc)
        self.ltc_tc_label.setText(add_tcs(self.tc, self.ltc_offset, 24))
        self.mtc_tc_label.setText(add_tcs(self.tc, self.mtc_offset, 24))

    def always_on_top(self):  # TEST
        self.is_pin = not self.is_pin
        if self.windowFlags() & Qt.WindowStaysOnTopHint:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.show()

    def lock(self):  # TEST
        self.is_lock = not self.is_lock
        if self.is_lock:
            self.ltc_frame.setEnabled(False)
            self.mtc_frame.setEnabled(False)
            self.audio_frame.setEnabled(False)
            self.play_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.clock_button.setEnabled(False)
            self.forward_button.setEnabled(False)
            self.backward_button.setEnabled(False)
            self.audio_slider.setEnabled(False)
            self.connect_button.setEnabled(False)
            self.ip_1.setEnabled(False)
            self.ip_2.setEnabled(False)
            self.ip_3.setEnabled(False)
            self.ip_4.setEnabled(False)
            self.reload_button.setEnabled(False)
            self.master_button.setEnabled(False)
            self.slave_button.setEnabled(False)
        else:
            if self.mode == "master":
                self.ltc_frame.setEnabled(True)
                self.mtc_frame.setEnabled(True)
                self.audio_frame.setEnabled(True)
                self.play_button.setEnabled(True)
                self.stop_button.setEnabled(True)
                self.clock_button.setEnabled(True)
                self.forward_button.setEnabled(True)
                self.backward_button.setEnabled(True)
                self.audio_slider.setEnabled(True)
                self.connect_button.setEnabled(True)
                self.ip_1.setEnabled(True)
                self.ip_2.setEnabled(True)
                self.ip_3.setEnabled(True)
                self.ip_4.setEnabled(True)
                self.reload_button.setEnabled(True)
                self.master_button.setEnabled(True)
                self.slave_button.setEnabled(True)
            elif self.mode == "slave":
                self.ltc_frame.setEnabled(True)
                self.mtc_frame.setEnabled(True)
                self.connect_button.setEnabled(True)
                self.ip_1.setEnabled(True)
                self.ip_2.setEnabled(True)
                self.ip_3.setEnabled(True)
                self.ip_4.setEnabled(True)
                self.reload_button.setEnabled(True)
                self.master_button.setEnabled(True)
                self.slave_button.setEnabled(True)

    # ----------------------AUDIO FUNCTIONS--------------------------

    def opne_audio(self):  # EMPTY
        pass

    def close_audio(self):  # EMPTY
        pass

    def set_gain(self):  # EMPTY
        pass

    def set_audio_device(self):  # EMPTY
        pass

    # ----------------------LTC FUNCTIONS--------------------------

    def set_ltc_state(self):  # TEST
        self.ltc_switch_state = not self.ltc_switch_state
        self.tc_thread.update_ltc_state()
        if self.ltc_switch_state:
            self.ltc_tc_label.setStyleSheet(f"color: {GREEN};")
            self.ltc_output_combo_box.setEnabled(False)
            self.ltc_fps_combo_box.setEnabled(False)
        else:
            self.ltc_tc_label.setText(self.ltc_offset)
            self.ltc_tc_label.setStyleSheet(f"color: {GRIS_4};")
            self.ltc_output_combo_box.setEnabled(True)
            self.ltc_fps_combo_box.setEnabled(True)

    def set_ltc_offset(self):  # TEST
        def errase_values():
            self.ltc_hh_offset.setText("")
            self.ltc_mm_offset.setText("")
            self.ltc_ss_offset.setText("")
            self.ltc_ff_offset.setText("")

        time_entries = [
            self.ltc_hh_offset.text(),
            self.ltc_mm_offset.text(),
            self.ltc_ss_offset.text(),
            self.ltc_ff_offset.text(),
        ]
        time_values = []

        for entry in time_entries:
            time_str = entry or "0"
            if not time_str.isdigit():
                errase_values()
                return
            time_values.append(int(time_str))

        hh, mm, ss, ff = time_values

        if hh > 23 or mm > 59 or ss > 59 or ff > self.ltc_fps - 1:
            errase_values()
            return

        new_time = f"{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}"

        self.ltc_offset = new_time
        self.ltc_offset_label.setText(new_time)

        if not self.ltc_switch_state or not self.is_playing:
            self.ltc_tc_label.setText(new_time)

        self.tc_thread.update_ltc_offset(self.ltc_offset)
        errase_values()

    def set_ltc_output(self):  # TEST
        device_name = self.ltc_output_combo_box.currentText()
        index = None

        for clave, valor in self.audio_devices.items():
            if valor == device_name:
                index = clave
                break

        if index is not None and isinstance(index, int):
            self.tc_thread.update_audio_device(index)

    def set_ltc_fps(self):  # TEST
        value = self.ltc_fps_combo_box.currentText()
        if value == "24 FPS":
            self.ltc_fps = 24
        elif value == "25 FPS":
            self.ltc_fps = 25
        elif value == "30 FPS":
            self.ltc_fps = 30
        self.tc_thread.update_ltc_fps(self.ltc_fps)

    # ----------------------MTC FUNCTIONS--------------------------

    def set_mtc_state(self):  # TEST
        self.mtc_switch_state = not self.mtc_switch_state
        self.tc_thread.update_mtc_state()
        if self.mtc_switch_state:
            self.mtc_tc_label.setStyleSheet(f"color: {GREEN};")
            self.mtc_output_combo_box.setEnabled(False)
            self.mtc_fps_combo_box.setEnabled(False)
        else:
            self.mtc_tc_label.setText(self.ltc_offset)
            self.mtc_tc_label.setStyleSheet(f"color: {GRIS_4};")
            self.mtc_output_combo_box.setEnabled(True)
            self.mtc_fps_combo_box.setEnabled(True)

    def set_mtc_offset(self):  # TEST
        def errase_values():
            self.mtc_hh_offset.setText("")
            self.mtc_mm_offset.setText("")
            self.mtc_ss_offset.setText("")
            self.mtc_ff_offset.setText("")

        time_entries = [
            self.mtc_hh_offset.text(),
            self.mtc_mm_offset.text(),
            self.mtc_ss_offset.text(),
            self.mtc_ff_offset.text(),
        ]
        time_values = []

        for entry in time_entries:
            time_str = entry or "0"
            if not time_str.isdigit():
                errase_values()
                return
            time_values.append(int(time_str))

        hh, mm, ss, ff = time_values

        if hh > 23 or mm > 59 or ss > 59 or ff > self.mtc_fps - 1:
            errase_values()
            return

        new_time = f"{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}"

        self.mtc_offset = new_time
        self.mtc_offset_label.setText(new_time)

        if not self.mtc_switch_state or not self.is_playing:
            self.mtc_tc_label.setText(new_time)

        self.tc_thread.update_mtc_offset(self.mtc_offset)
        errase_values()

    def set_mtc_output(self):  # TEST
        device_name = self.mtc_output_combo_box.currentText()
        index = None

        for clave, valor in self.midi_devices.items():
            if valor == device_name:
                index = clave
                break

        if index is not None and isinstance(index, int):
            self.tc_thread.update_midi_device(index)

    def set_mtc_fps(self):  # TEST
        value = self.mtc_fps_combo_box.currentText()
        if value == "24 FPS":
            self.mtc_fps = 24
        elif value == "25 FPS":
            self.mtc_fps = 25
        elif value == "30 FPS":
            self.mtc_fps = 30
        self.tc_thread.update_mtc_fps(self.mtc_fps)


# -------------------------THREADS--------------------------


class TC_Thread(QtCore.QThread):
    tc_data = QtCore.pyqtSignal(str)
    ltc_data = QtCore.pyqtSignal(str)
    mtc_data = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(TC_Thread, self).__init__(parent)
        self.parent = parent
        self.is_open = True
        self.ltc_tc = None
        self.mtc_tc = None
        self.tc = None
        self.ltc_switch = None
        self.mtc_switch = None
        self.ltc_offset = None
        self.mtc_offset = None
        self.ltc_fps = None
        self.mtc_fps = None
        self.audio_devices = None
        self.midi_devices = None

    def init(self):
        self.is_running = True
        self.ltc_tc = self.parent.ltc_tc
        self.mtc_tc = self.parent.mtc_tc
        self.tc = self.parent.tc
        self.ltc_switch = self.parent.ltc_switch_state
        self.mtc_switch = self.parent.mtc_switch_state
        self.ltc_offset = self.parent.ltc_offset
        self.mtc_offset = self.parent.mtc_offset
        self.ltc_fps = self.parent.ltc_fps
        self.mtc_fps = self.parent.mtc_fps
        self.audio_device = AudioDevice()
        self.midi_device = MidiDevice()

    def run(self):
        self.tc = Timecode(24, self.tc)
        self.ltc_tc = Timecode(self.ltc_fps, self.ltc_tc)
        self.mtc_tc = Timecode(self.mtc_fps, self.mtc_tc)

        while True:
            self.tc.next()
            if self.ltc_switch:
                self.ltc_tc = add_tcs(self.ltc_offset, self.tc, self.ltc_fps)
                audiodata = LTC.make_ltc_audio(self.ltc_tc)
                if self.audio_device.stream:
                    self.audio_device.play(audiodata)
            if self.mtc_switch:
                self.mtc_tc = add_tcs(self.mtc_offset, self.tc, self.mtc_fps)
                if self.midi_device.midi_out:
                    self.midi_device.sendMTC(self.mtc_tc)
            self.tc_data.emit(str(self.tc))
            self.ltc_data.emit(str(self.ltc_tc))
            self.mtc_data.emit(str(self.mtc_tc))
            time.sleep(1 / 24)

    def update_tc(self, tc):
        self.tc = tc

    def update_ltc_state(self):
        self.ltc_switch = not self.ltc_switch

    def update_mtc_state(self):
        self.mtc_switch = not self.mtc_switch

    def update_ltc_offset(self, offset):
        self.ltc_offset = offset

    def update_mtc_offset(self, offset):
        self.mtc_offset = offset

    def update_ltc_fps(self, fps):
        self.ltc_fps = fps

    def update_mtc_fps(self, fps):
        self.mtc_fps = fps

    def update_audio_device(self, device_index):
        self.audio_device.set_output_device(device_index)

    def update_midi_device(self, device_index):
        self.midi_device.set_output_device(device_index)

    def get_audio_devices(self):
        self.audio_devices = self.audio_device.get_output_devices()

    def get_midi_devices(self):
        self.midi_devices = self.midi_device.get_all_output_devices()

    def stop(self):
        self.is_running = False
        self.midi_device.clear()
        self.audio_device.clear()
        self.is_open = False
        self.terminate()


class Player_Thread(QtCore.QThread):
    player_data = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(Player_Thread, self).__init__(parent)
        self.parent = parent
        self.is_running = True

    def init(self):
        self.audio_device = AudioDevice()

    def run(self):
        pass

    def open_file(self):
        pass

    def close_file(self):
        self.stop()

    def stop(self):
        self.audio_device.clear()


class Server_Thread(QtCore.QThread):
    player_data = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(Server_Thread, self).__init__(parent)
        self.parent = parent
        self.is_running = True
        self.ip = self.parent.ip
        self.port = self.parent.port

    def init(self):
        self.server = Server(self.ip, self.port)

    def run(self):
        self.server.start()

    def change_ip(self, ip, port):
        self.server.stop()
        self.server = Server(self.ip, self.port)
        self.run()

    def stop(self):
        self.server.stop()

    def send_tc_over_lan(self, message):
        self.server.send_to_all(message)


class Client_Thread(QtCore.QThread):
    player_data = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(Client_Thread, self).__init__(parent)
        self.parent = parent
        self.is_running = True

    def init(self):
        self.client = Client()

    def run(self):
        pass

    def change_ip(self):
        pass

    def stop(self):
        pass


# --------------------------EXEC----------------------------


def main():
    mainApp = QApplication(sys.argv)
    app = UI()
    mainApp.exec_()


if __name__ == "__main__":
    main()
