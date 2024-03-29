import time
import sys
import os
import inspect
import copy

from concurrent.futures import ThreadPoolExecutor

from PyQt5 import uic, QtCore,QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QColor, QIcon

from socket import *
import sounddevice as sd
from functools import partial

from tools import *
from get_nets import get_nets,is_ip_address
from User_GUI import UsersWindow

##############################################
##----------------- PATHS ------------------##
##############################################

actual_path = os.path.abspath(os.path.dirname(__file__))
gui_ui_path = os.path.join(actual_path, "gui.ui")
icon_url = os.path.join(actual_path, "img/AppIcon2.png").replace("\\", "/")
close_img_url = os.path.join(actual_path, "img/close.png").replace("\\", "/")
close_hover_img_url = os.path.join(actual_path, "img/close_on.png").replace("\\", "/")
min_img_url = os.path.join(actual_path, "img/min.png").replace("\\", "/")
min_hover_img_url = os.path.join(actual_path, "img/min_on.png").replace("\\", "/")
arrow_img_url = os.path.join(actual_path, "img/arrow2.png").replace("\\", "/")
arrow_disable_img_url = os.path.join(actual_path, "img/arrow_disable.png").replace("\\", "/")
client_button_img_url = os.path.join(actual_path, "img/People.png").replace("\\", "/")
client_button_disable_img_url = os.path.join(actual_path, "img/People_disable.png").replace("\\", "/")


##############################################
##------------------- GUI ------------------##
##############################################

class GUI(QMainWindow):

    def __init__(self, network_pipe, player_pipe, ltc_pipe, mtc_pipe, main_pipe):#TEST
        
        try:
            super(GUI,self).__init__()
            uic.loadUi(gui_ui_path,self)
            self.setWindowTitle("SDM-Timecode")
            self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
            self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
            self.setWindowIcon(QIcon(icon_url))
            self.set_styles()
            self.var_init()
            self.thread_init(network_pipe,player_pipe,ltc_pipe,mtc_pipe,main_pipe)
            self.func_init()
            self.visual_init()
            self.show()
            self.main_pipe.send({"loading":False})
            
        except Exception as e:
            log(f"[ERROR GUI {inspect.currentframe().f_code.co_name}]: {e}")

    # ---------------- INIT CONFIG

    def set_styles(self):

        close_button_style = f"""QPushButton {{
            image: url("{close_img_url}");
                color: #454545;
                border: none;
                border-radius: 5px;
            }}
            QPushButton:hover {{
            image: url("{close_hover_img_url}");
            background-repeat: no-repeat;
                background-color: #202020;
                color: #202020;
            }}
            QPushButton:pressed {{
                background-color: #FFFFFF;
                border-style: inset;
            }}"""

        min_button_style = f"""QPushButton {{
            image: url("{min_img_url}");
                color: #454545;
                border: none;
                border-radius: 5px;
            }}
            QPushButton:hover {{
            image: url("{min_hover_img_url}");
            background-repeat: no-repeat;
                background-color: #202020;
                color: #202020;
            }}
            QPushButton:pressed {{
                background-color: #FFFFFF;
                border-style: inset;
            }}"""

        combo_box_style = f"""QComboBox {{
            background-color: #202020;
            color: grey;
            border: 1px solid #606060;
            border-radius: 2px;
            padding: 2px;
            padding-left:5px;
        }}

        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left-width: 1px;
            border-left-color: #606060;
            border-left-style: solid;
            background: #333333;
        }}

        QComboBox::drop-down::hover {{
            background: #404040;
        }}

        QComboBox::drop-down::pressed {{
            background: #505050;
        }}


        QComboBox::down-arrow {{
            image: url("{arrow_img_url}");
            width: 10px;
        }}

        QComboBox QAbstractItemView {{
            border-radius:0;
            border-bottom-right-radius: 2px;
            border-bottom-left-radius: 2px;
            background: #303030;
            border: 1px solid #404040;
            padding: 4px 4px 4px 4px;
            color: grey;
        }}

        QComboBox:disabled  {{
            background-color:  transparent;
            color: #505050;
            border: 1px solid #404040;
            border-radius: 4px;
            padding: 2px;
            padding-left:5px;
        }}

        QComboBox::drop-down::disabled  {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left-width: 1px;
            border-left-color: #404040;
            border-left-style: solid;
            background: transparent;
        }}

        QComboBox::down-arrow::disabled {{
            image: url("{arrow_disable_img_url}");
            width: 10px;
        }}
        """

        self.ltc_output_combo_box.setStyleSheet(combo_box_style)
        self.ltc_fps_combo_box.setStyleSheet(combo_box_style)
        self.mtc_output_combo_box.setStyleSheet(combo_box_style)
        self.mtc_fps_combo_box.setStyleSheet(combo_box_style)
        self.audio_output_combo_box.setStyleSheet(combo_box_style)
        self.app_mini_button.setStyleSheet(min_button_style)
        self.app_close_button.setStyleSheet(close_button_style)
        self.audio_close_button.setStyleSheet(close_button_style)
        
    def var_init(self): #TEST
        self.is_running = True
        
        self.is_lock = False
        self.is_pin = False
        
        # -- PLAYER VARS
        # PLAYER SEND
        self.is_playing = False
        self.time_start = 0
        self.audio_data = None
        self.sample_rate = None
        
        self.audio_devices = self.get_output_devices()
        self.audio_device = next(iter(self.audio_devices))
        self.paused_sample = 0
        self.gain = 0.8
        self.is_paused = False
        
        # PLAYER RECV
        self.current_sample = 0
        
        # OTHERS
        self.audio_total_duration = None
        
        # -- SERVER VARS
        # SERVER SEND
        self.nets = get_nets()
        self.host = "192.168.0.1"
        self.network_is_on = False
        self.timecode = 0
        self.mode = "master"
        # SERVER RECV
        self.online = False
        self.server_error = None
        self.clients = []
        
        self.users_window = None
        
        # -- LTC SENDER
        # LTC SEND
        self.ltc_output_device = 0
        self.ltc_fps = 24
        self.ltc_offset = 0
        self.ltc_is_on = False

        # -- MTC SENDER
        # MTC SEND
        self.mtc_output_device = 0
        self.mtc_fps = 24
        self.mtc_offset = 0
        self.mtc_is_on = False

    def thread_init(self, network_pipe, player_pipe, ltc_pipe, mtc_pipe, main_pipe):#TEST
        self.main_pipe = main_pipe
        self.server_pipe = network_pipe
        self.player_pipe = player_pipe
        self.ltc_pipe = ltc_pipe
        self.mtc_pipe = mtc_pipe
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_tc_labels)
        self.timer.setInterval(50)
        self.timer.start()
        
        self.signal_object = SignalObject()
        self.signal_object.valueChanged.connect(self.update_network_label)
        
        self.executor = ThreadPoolExecutor()
        self.recv_server_thread = self.executor.submit(self.recv_server_data)
        self.recv_player_thread = self.executor.submit(self.recv_player_data)
        self.send_thread = self.executor.submit(self.send_data_to_process)

    def func_init(self): #TEST
        # WINDOW BUTTONS ASSING
        self.app_mini_button.clicked.connect(self.showMinimized)
        self.app_close_button.clicked.connect(self.close_app)
        self.main_frame_2.mouseMoveEvent = self.mouseMoveWindow
        
        # NETWORK AND MODE BUTTONS ASSING
        self.master_button.clicked.connect(self.set_master_mode)
        self.slave_button.clicked.connect(self.set_slave_mode)
        self.connect_button.clicked.connect(self.set_network)
        self.client_button.clicked.connect(self.set_users_window)
        self.client_add_button.clicked.connect(self.add_client)

        # CONTROL BUTTONS ASSING
        self.play_button.clicked.connect(self.play_pause)
        self.stop_button.clicked.connect(self.stop)
        self.clock_button.clicked.connect(self.tc_clock)
        self.forward_button.clicked.connect(self.forward)
        self.backward_button.clicked.connect(self.backward)
        self.pin_button.clicked.connect(self.always_on_top)
        self.lock_button.clicked.connect(self.lock)
        
        # AUDIO BUTTONS ASSING
        self.audio_open_button.clicked.connect(self.open_audio_file)
        self.audio_close_button.clicked.connect(self.close_audio_file)
        self.audio_slider.valueChanged.connect(self.set_gain)
        self.audio_output_combo_box.currentIndexChanged.connect(self.set_audio_device)
        
        #LTC BUTTONS ASSING
        self.ltc_switch.clicked.connect(self.set_ltc_on)
        self.ltc_offset_button.clicked.connect(self.set_ltc_offset)
        self.ltc_output_combo_box.currentIndexChanged.connect(self.set_ltc_output)
        self.ltc_fps_combo_box.currentIndexChanged.connect(self.set_ltc_fps)
        
        # MTC BUTTONS ASSING
        self.mtc_switch.stateChanged.connect(self.set_mtc_on)
        self.mtc_offset_button.clicked.connect(self.set_mtc_offset)
        self.mtc_output_combo_box.currentIndexChanged.connect(self.set_mtc_output)
        self.mtc_fps_combo_box.currentIndexChanged.connect(self.set_mtc_fps)

    def visual_init(self): #TEST
        
        if self.audio_devices != {}:
            list_audio_devices = list(self.audio_devices.values())
            self.audio_output_combo_box.clear()
            self.audio_output_combo_box.addItems(list_audio_devices)
            self.ltc_output_combo_box.clear()
            self.ltc_output_combo_box.addItems(list_audio_devices)
        
        if self.nets:
            ip = str(next(iter(self.nets.values())))
            if is_ip_address(ip):
                ip_components = ip.split(".")
                ip1, ip2, ip3, ip4 = ip_components
            else:
                log("La dirección IP no es válida",WARNING)
                # Realiza alguna acción para manejar el caso de una dirección IP no válida
        else:
            ip_components = self.host.split(".")
            ip1, ip2, ip3, ip4 = ip_components
            
        self.ip_1.setText(ip1)
        self.ip_2.setText(ip2)
        self.ip_3.setText(ip3)
        self.ip_4.setText(ip4)
        
        self.audio_slider.setValue(int(self.gain*100))
        self.error_label.setVisible(False)
        self.recv_mtc_data()   

        self.remaning_tc.setText(str(secs_to_tc(86400)))
        
        # ICON
        pixmap = QPixmap("img/icon.ico")
        pixmap_redimensionado = pixmap.scaled(15, 15) 
        transparencia = 150
        painter = QPainter(pixmap_redimensionado)
        painter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
        painter.fillRect(pixmap_redimensionado.rect(), QColor(0, 0, 0, transparencia))
        painter.end()
        self.icon.setPixmap(pixmap_redimensionado)
        self.icon.show()

    # ---------------- WINDOW CONFIG

    def mousePressEvent(self, event):#
        self.oldPosition = event.globalPos()

    def mouseMoveWindow(self, event):#
        if not self.isMaximized() and hasattr(self, 'oldPosition'):
            delta = QtCore.QPoint(event.globalPos() - self.oldPosition)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPosition = event.globalPos()

    def close_app(self): #TEST
        self.is_running = False
        self.main_pipe.send({"finish":True})

    # ---------------- BUTTONS FUNCTIONS

    # NETWORK AND MODE BUTTONS FUNCTIONS

    def set_master_mode(self): #TEST       
        self.master_button.setChecked(True)
        self.slave_button.setChecked(False)
            
        if self.mode == "master":
            return
        self.mode = "master"
        self.stop()
        
        self.play_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.clock_button.setEnabled(True)
        self.forward_button.setEnabled(True)
        self.backward_button.setEnabled(True)
        self.audio_open_button.setEnabled(True)
        self.audio_close_button.setEnabled(True)
        self.audio_slider.setEnabled(True)
        self.audio_output_combo_box.setEnabled(True)
        self.audio_open_button.setText("OPEN AN AUDIO FILE")
        self.client_button.setVisible(True)
        self.users_label.setVisible(True)
        self.client_add_button.setEnabled(True)
        
        if self.network_is_on:
            self.set_network()
            self.set_user_button_icon(1)
        else:
            self.connect_button.setText("START SERVER")
            self.set_user_button_icon(0)

        self.ltc_pipe.send({"is_playing":False})
        self.mtc_pipe.send({"is_playing":False})
        self.timecode = 0

    def set_slave_mode(self): #TEST
        
        if self.is_playing:
            if not self.confirm_stop_window():
                self.master_button.setChecked(True)
                self.slave_button.setChecked(False)
                return
            self.stop()
            
        self.player_pipe.send({"file_path":None})
        
        self.master_button.setChecked(False)
        self.slave_button.setChecked(True)
        
        if self.mode == "slave":
            return
        self.mode = "slave"

        self.play_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.clock_button.setEnabled(False)
        self.forward_button.setEnabled(False)
        self.backward_button.setEnabled(False)
        self.audio_open_button.setEnabled(False)
        self.audio_close_button.setEnabled(False)
        self.audio_slider.setEnabled(False)
        self.audio_output_combo_box.setEnabled(False)
        self.audio_open_button.setText("AUDIO PLAYER IS DISABLE IN SLAVE MODE")
        self.client_button.setVisible(False)
        self.users_label.setVisible(False)
        self.client_add_button.setEnabled(False)
        
        if self.network_is_on:
            self.set_network()
        else:
            self.connect_button.setText("CONNECT")
        
        self.ltc_pipe.send({"is_playing":True})
        self.mtc_pipe.send({"is_playing":True})
        self.timecode = 0
        
        if self.users_window is not None:
            self.users_window.close()
            self.users_window = None
        
    def set_network(self): #TEST
        self.set_ip()
        self.network_is_on = not self.network_is_on
        
        if not self.network_is_on:
            if self.mode == "master":
                self.connect_button.setText("START SERVER")
                self.set_user_button_icon(1)
            elif self.mode == "slave":
                self.connect_button.setText("CONNECT")
            self.connect_button.setStyleSheet(start_button_style)
            self.error_label.setVisible(False)
            self.ip_1.setEnabled(True)
            self.ip_2.setEnabled(True)
            self.ip_3.setEnabled(True)
            self.ip_4.setEnabled(True)
            
        else:
            self.set_user_button_icon(0)
            if not self.online and self.server_error is None:
                self.connect_button.setText("CONNECTING")
                self.connect_button.setStyleSheet(connecting_button_style)
                if self.mode=="slave":
                    self.ip_1.setEnabled(False)
                    self.ip_2.setEnabled(False)
                    self.ip_3.setEnabled(False)
                    self.ip_4.setEnabled(False)
                self.error_label.setVisible(False)
                self.error_label.setText(self.server_error) 
        
        if self.mode == "slave":
            self.timecode = 0

    def set_ip(self):
        try:
            
            ip1 = int(self.ip_1.text())
            self.ip_1.setText(str(ip1))
            
            ip2 = int(self.ip_2.text())
            self.ip_2.setText(str(ip2))
            
            ip3 = int(self.ip_3.text())
            self.ip_3.setText(str(ip3))
            
            ip4 = int(self.ip_4.text())
            self.ip_4.setText(str(ip4))
            
        except ValueError:
            ip1 = self.ip_1.text()
            ip2 = self.ip_2.text()
            ip3 = self.ip_3.text()
            ip4 = self.ip_4.text()

        self.host = f"{ip1}.{ip2}.{ip3}.{ip4}"
        
    # CONTROLS BUTTONS FUNCTIONS

    def play_pause(self): #TEST
        self.is_playing = not self.is_playing
        self.send_play_status()

    def stop(self): #TEST
        self.is_playing = False
        self.send_play_status()
        self.player_pipe.send({"stop":True})
        self.play_button.setChecked(False)

    def tc_clock(self): #TEST
        if self.audio_total_duration is None:
            self.is_playing = True
            self.send_play_status()
            self.player_pipe.send({"clock":True})
            self.play_button.setChecked(True)

    def forward(self): #TEST
        self.player_pipe.send({"forward":True})

    def backward(self): #TEST
        self.player_pipe.send({"backward":True})

    def always_on_top(self): #TEST
        self.is_pin= not self.is_pin
        if self.windowFlags() & Qt.WindowStaysOnTopHint:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.show()

    def lock(self): #TEST
        
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
            self.client_add_button.setEnabled(False)
            self.master_button.setEnabled(False)
            self.slave_button.setEnabled(False)
            
        else:
            self.master_button.setEnabled(True)
            self.slave_button.setEnabled(True)
            self.ltc_frame.setEnabled(True)
            self.mtc_frame.setEnabled(True)
            self.connect_button.setEnabled(True)
            self.ip_1.setEnabled(True)
            self.ip_2.setEnabled(True)
            self.ip_3.setEnabled(True)
            self.ip_4.setEnabled(True)
            
            if self.mode == "master":
                self.audio_frame.setEnabled(True)
                self.play_button.setEnabled(True)
                self.stop_button.setEnabled(True)
                self.clock_button.setEnabled(True)
                self.forward_button.setEnabled(True)
                self.backward_button.setEnabled(True)
                self.audio_slider.setEnabled(True)
                self.connect_button.setEnabled(True)
                self.client_add_button.setEnabled(True)

    # PLAYER BUTTONS FUNCTIONS

    def open_audio_file(self): #TEST
        try:
            file_path, _ = QFileDialog.getOpenFileName(None, 'Abrir archivo de audio', '', 'Archivos de audio (*.wav *.mp3)')
            
            if not file_path:
                return
        
            if self.is_playing:
                if not self.confirm_stop_window():
                    return
            
            self.stop()
            self.player_pipe.send({"file_path":str(file_path)})
            file_name = os.path.basename(file_path)
            self.audio_open_button.setText(file_name.upper())
            
        except Exception as e:
            log('[OPEN AUDIO ERROR]:', str(e))
            self.close_audio_file()

    def close_audio_file(self): #TEST
        if self.audio_total_duration is not None:
            if self.is_playing:
                if not self.confirm_stop_window():
                    return
            
            self.stop()
            self.player_pipe.send({"file_path":None})
            self.audio_open_button.setText("OPEN AN AUDIO FILE TO PLAY")

    def set_gain(self): #TEST
        self.gain = self.audio_slider.value()/100

    def set_audio_device(self): #TEST

        if self.audio_devices != {}:
            device_name = self.audio_output_combo_box.currentText()
            for key, value in self.audio_devices.items():
                if value == device_name:
                    device_index = key
                    self.audio_device = device_index
                    break
                
        if self.is_playing:
            self.play_pause()
            time.sleep(0.01)
            self.play_pause()

    # LTC BUTTONS FUNCTIONS

    def set_ltc_on(self): #TEST
        self.ltc_is_on = not self.ltc_is_on
        if self.ltc_is_on:
            self.ltc_tc_label.setText(secs_to_tc(self.ltc_offset+self.timecode,self.ltc_fps))
            self.ltc_tc_label.setStyleSheet(f"color: #36BD74;")
        else:
            self.ltc_tc_label.setText(secs_to_tc(self.ltc_offset,self.ltc_fps))
            self.ltc_tc_label.setStyleSheet(f"color: grey;")

    def set_ltc_offset(self): #TEST
        
        def errase_values():
            self.ltc_hh_offset.setText("")
            self.ltc_mm_offset.setText("")
            self.ltc_ss_offset.setText("")
            self.ltc_ff_offset.setText("")     
               
        time_entries = [self.ltc_hh_offset.text(), self.ltc_mm_offset.text(),self.ltc_ss_offset.text(),self.ltc_ff_offset.text()]
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
        new_time_sec = tc_to_secs(new_time,self.ltc_fps)
        self.ltc_offset = new_time_sec
        self.ltc_offset_label.setText(new_time)
        
        if not self.ltc_is_on or not self.is_playing:
            self.ltc_tc_label.setText(new_time)
            
        errase_values()

    def set_ltc_output(self): #TEST
        if self.audio_devices != {}:
            device_name = self.ltc_output_combo_box.currentText()
            for key, value in self.audio_devices.items():
                if value == device_name:
                    device_index = key
                    self.ltc_output_device = device_index
                    break

    def set_ltc_fps(self): #TEST
        value = self.ltc_fps_combo_box.currentText()
        if value == "24 FPS":
            self.ltc_fps = 24
        elif value == "25 FPS":
            self.ltc_fps = 25
        elif value == "30 FPS":
            self.ltc_fps = 30

    # MTC BUTTONS FUNCTIONS

    def set_mtc_on(self): #TEST
        self.mtc_is_on = not self.mtc_is_on
        if self.mtc_is_on:
            self.mtc_tc_label.setText(secs_to_tc(self.mtc_offset + self.timecode,self.mtc_fps))
            self.mtc_tc_label.setStyleSheet(f"color: #36BD74;")
        else:
            self.mtc_tc_label.setText(secs_to_tc(self.mtc_offset,self.mtc_fps))
            self.mtc_tc_label.setStyleSheet(f"color: grey;")

    def set_mtc_offset(self): #TEST  
        def errase_values():
            self.mtc_hh_offset.setText("")
            self.mtc_mm_offset.setText("")
            self.mtc_ss_offset.setText("")
            self.mtc_ff_offset.setText("")     
               
        time_entries = [self.mtc_hh_offset.text(), self.mtc_mm_offset.text(),self.mtc_ss_offset.text(),self.mtc_ff_offset.text()]
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
        new_time_sec = tc_to_secs(new_time,self.mtc_fps)
        
        self.mtc_offset = new_time_sec
        self.mtc_offset_label.setText(new_time)
        
        if not self.mtc_is_on or not self.is_playing:
            self.mtc_tc_label.setText(new_time)
        
        errase_values()

    def set_mtc_output(self): #TEST
        if self.mtc_outputs != {}:
            device_name = self.mtc_output_combo_box.currentText()
            for key, value in self.mtc_outputs.items():
                if value == device_name:
                    device_index = key
                    self.mtc_output_device = device_index
                    break

    def set_mtc_fps(self): #TEST
        value = self.mtc_fps_combo_box.currentText()
        if value == "24 FPS":
            self.mtc_fps = 24
        elif value == "25 FPS":
            self.mtc_fps = 25
        elif value == "30 FPS":
            self.mtc_fps = 30

    # ---------------- TOOLS

    def get_output_devices(self): #TEST
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

    def center_widget(self,window):#TEST
        window.setGeometry(
            QtWidgets.QStyle.alignedRect(
                QtCore.Qt.LeftToRight,
                QtCore.Qt.AlignCenter,
                window.size(),
                self.geometry(),
            )
        )

    def confirm_stop_window(self):#TEST
        message_box = QMessageBox(self)
        message_box.setWindowTitle("Warning")
        message_box.setText("Timecode is playing!")
        message_box.setInformativeText("Do you want to stop it?")
        message_box.setIcon(QMessageBox.Question)
        message_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        wrapper = partial(self.center_widget, message_box)
        QtCore.QTimer.singleShot(0, wrapper)
        message_box.setStyleSheet(message_box_style)
        message_box.setWindowFlags(message_box.windowFlags() | Qt.FramelessWindowHint)
        reply = message_box.exec_()

        return reply == QMessageBox.Yes
    
    def set_users_window(self):
        if self.users_window is None:
            self.users_window = UsersWindow(self)
            self.users_window.show()
            self.users_window.itemClicked.connect(self.remove_client)
            self.users_window.update_lists(self.clients)
        else:
            self.users_window.close()
            self.users_window = None

    def is_valid_ipv4_address(ip):
        parts = ip.split(".")
        
        if len(parts) != 4:
            return False
        
        for part in parts:
            try:
                value = int(part)
                if value < 0 or value > 255:
                    return False
            except ValueError:
                return False
        
        return True
    
    # ---------------- THREAD FUNCTIONS (PIPES COMUNICATION)

    def send_play_status(self):
        try:
            data_to_send = {"is_playing":self.is_playing}
            if self.mode == "master":
                self.player_pipe.send(data_to_send)
            self.ltc_pipe.send(data_to_send)
            self.mtc_pipe.send(data_to_send)
        except Exception as e:
            log(f"[ERROR GUI {inspect.currentframe().f_code.co_name}]: {e}")

    def send_data_to_process(self): #THREAD
        try:
            # SEND CONFIRMATIONS
            last_is_running = self.is_running
            last_audio_device = self.audio_device
            last_gain = self.gain
            
            last_host = self.host
            last_network_is_on = self.network_is_on
            last_timecode = self.timecode
            last_mode = self.mode
            last_clients = copy.deepcopy(self.clients)
            
            last_ltc_output_device = self.ltc_output_device
            last_ltc_fps = self.ltc_fps
            last_ltc_offset = self.ltc_offset
            last_ltc_is_on = self.ltc_is_on
            
            last_mtc_output_device = self.mtc_output_device
            last_mtc_fps = self.mtc_fps
            last_mtc_offset = self.mtc_offset
            last_mtc_is_on = self.mtc_is_on
            
            while self.is_running:
                data_to_send = {}
                
                if last_timecode != self.timecode:
                    data_to_send['tc'] = self.timecode
                    if self.mode == "master":
                        self.server_pipe.send(data_to_send)
                    self.ltc_pipe.send(data_to_send)
                    self.mtc_pipe.send(data_to_send)
                    last_timecode = self.timecode
                    
                if last_audio_device != self.audio_device:
                    data_to_send['audio_device'] = self.audio_device
                    self.player_pipe.send(data_to_send)        
                    last_audio_device = self.audio_device         
                    
                if last_gain != self.gain:
                    data_to_send['gain'] = self.gain
                    self.player_pipe.send(data_to_send)          
                    last_gain = self.gain        
                    
                if last_host != self.host:
                    data_to_send['host'] = self.host
                    self.server_pipe.send(data_to_send)        
                    last_host = self.host
                    
                if last_network_is_on != self.network_is_on:
                    data_to_send['network_is_on'] = self.network_is_on
                    self.server_pipe.send(data_to_send)        
                    last_network_is_on = self.network_is_on 
                    
                if last_mode != self.mode:
                    data_to_send['mode'] = self.mode
                    self.server_pipe.send(data_to_send)         
                    last_mode = self.mode   
                    
                if last_clients != self.clients:
                    data_to_send['clients'] = self.clients
                    self.server_pipe.send(data_to_send)
                    last_clients = copy.deepcopy(self.clients)  
                    
                if last_ltc_is_on != self.ltc_is_on:
                    data_to_send['ltc_is_on'] = self.ltc_is_on
                    self.ltc_pipe.send(data_to_send)          
                    last_ltc_is_on = self.ltc_is_on   
                    
                if last_ltc_output_device != self.ltc_output_device:
                    data_to_send['ltc_output_device'] = self.ltc_output_device
                    self.ltc_pipe.send(data_to_send)           
                    last_ltc_output_device = self.ltc_output_device 
                    
                if last_ltc_fps != self.ltc_fps:
                    data_to_send['ltc_fps'] = self.ltc_fps
                    self.ltc_pipe.send(data_to_send)   
                    last_ltc_fps = self.ltc_fps
                    
                if last_ltc_offset != self.ltc_offset:
                    data_to_send['ltc_offset'] = self.ltc_offset
                    self.ltc_pipe.send(data_to_send)   
                    last_ltc_offset = self.ltc_offset
                    
                if last_mtc_is_on != self.mtc_is_on:
                    data_to_send['mtc_is_on'] = self.mtc_is_on
                    self.mtc_pipe.send(data_to_send)           
                    last_mtc_is_on = self.mtc_is_on   
                    
                if last_mtc_output_device != self.mtc_output_device:
                    data_to_send['mtc_output_device'] = self.mtc_output_device
                    self.mtc_pipe.send(data_to_send)           
                    last_mtc_output_device = self.mtc_output_device
                    
                if last_mtc_fps != self.mtc_fps:
                    data_to_send['mtc_fps'] = self.mtc_fps
                    self.mtc_pipe.send(data_to_send)   
                    last_mtc_fps = self.mtc_fps 
                    
                if last_mtc_offset != self.mtc_offset:
                    data_to_send['mtc_offset'] = self.mtc_offset
                    self.mtc_pipe.send(data_to_send)   
                    last_mtc_offset = self.mtc_offset
                    
                if last_is_running != self.is_running:
                    data_to_send['is_running'] = self.is_running
                    self.server_pipe.send(data_to_send)   
                    self.player_pipe.send(data_to_send) 
                    self.ltc_pipe.send(data_to_send) 
                    self.mtc_pipe.send(data_to_send) 
                    last_is_running = self.is_running
                
                time.sleep(0.01)
                
        except Exception as e:
            log(f"[ERROR GUI {inspect.currentframe().f_code.co_name}]: {e}")

    def recv_server_data(self): #THREAD
        try:
            self.users_label.setText("0")            
            while self.is_running:
                
                network_recv_data = self.server_pipe.recv()

                if 'online' in network_recv_data:
                    self.online = network_recv_data["online"]
                    
                if 'error' in network_recv_data:
                    self.server_error = network_recv_data["error"]

                if 'timecode_recv' in network_recv_data and self.mode == "slave":
                    self.timecode = network_recv_data["timecode_recv"]
                    
                #UPDATE VALUES
                if 'online' in network_recv_data or 'error' in network_recv_data:
                    self.signal_object.valueChanged.emit()
                
        except Exception as e:
            log(f"[ERROR GUI {inspect.currentframe().f_code.co_name}]: {e}")

    def recv_player_data(self): #THREAD
        try:
            while self.is_running:
                
                player_recv_data = self.player_pipe.recv()
                
                if 'tc' in player_recv_data and self.mode == "master":
                    self.timecode = player_recv_data["tc"]

                    if self.timecode == self.audio_total_duration:
                        self.stop()
                    
                if 'total_duration' in player_recv_data:
                    self.audio_total_duration = player_recv_data["total_duration"]
                    if self.audio_total_duration is not None:
                        self.remaining_time = self.audio_total_duration
                        self.remaning_tc.setText(str(secs_to_tc(self.audio_total_duration - self.timecode))) 
                    else:
                        self.remaining_time = 86400
                        self.remaning_tc.setText(str(secs_to_tc(86400 - self.timecode))) 
                
        except Exception as e:
            log(f"[ERROR GUI {inspect.currentframe().f_code.co_name}]: {e}")

    def recv_ltc_data(self): #THREAD
        try:
            recive_data = self.mtc_pipe.recv()
            
            if 'ltc_devices' in recive_data:
                self.ltc_outputs = recive_data["ltc_devices"]
                if self.ltc_outputs != {}:
                    self.ltc_output_combo_box.clear()
                    self.ltc_output_combo_box.addItems(list(self.ltc_outputs.values()))
        except Exception as e:
            log(f"[ERROR GUI {inspect.currentframe().f_code.co_name}]: {e}")

    def recv_mtc_data(self): #THREAD
        try:
            recive_data = self.mtc_pipe.recv()
            
            if 'mtc_devices' in recive_data:
                self.mtc_outputs = recive_data["mtc_devices"]
                if self.mtc_outputs != {}:
                    self.mtc_output_combo_box.clear()
                    self.mtc_output_combo_box.addItems(list(self.mtc_outputs.values()))
        except Exception as e:
            log(f"[ERROR GUI {inspect.currentframe().f_code.co_name}]: {e}")

    # ---------------- UPDATES FUNCTIONS

    def update_tc_labels(self):
        tc = secs_to_tc(self.timecode)
        self.tc_label.setText(str(tc))

        if self.audio_total_duration is None:
            remaining_tc = secs_to_tc(86400 - self.timecode)
        else:
            remaining_tc = secs_to_tc(self.audio_total_duration - self.timecode)
        self.remaning_tc.setText(str(remaining_tc))
        
        if self.ltc_is_on:
            ltc_tc = secs_to_tc(self.timecode + self.ltc_offset, self.ltc_fps)
            self.ltc_tc_label.setText(str(ltc_tc))
        
        if self.mtc_is_on:
            mtc_tc = secs_to_tc(self.timecode + self.mtc_offset, self.mtc_fps)
            self.mtc_tc_label.setText(str(mtc_tc))

    def update_network_label(self):
        if self.online and self.network_is_on:
            
            if self.mode=="master":
                self.connect_button.setText("SENDING")
                
            elif self.mode=="slave":
                self.connect_button.setText("LISTENING")
            self.connect_button.setStyleSheet(online_button_style)
            self.error_label.setVisible(False)
            self.error_label.setText(self.server_error)
            
        elif not self.online and self.network_is_on and self.server_error is not None:
            
            if self.server_error == "SERVER NOT FOUND":
                self.connect_button.setText("TRYING")
                self.connect_button.setStyleSheet(connecting_button_style)
                
            else:
                self.connect_button.setText("ERROR")
                self.connect_button.setStyleSheet(offline_button_style)
                
            self.error_label.setVisible(True)
            self.error_label.setText(self.server_error)

    def update_clients_number(self):
        users_total = str(len(self.clients))
        self.users_label.setText(users_total)

    def add_client(self):
        try:
            
            ip1 = int(self.ip_1.text())
            self.ip_1.setText(str(ip1))
            
            ip2 = int(self.ip_2.text())
            self.ip_2.setText(str(ip2))
            
            ip3 = int(self.ip_3.text())
            self.ip_3.setText(str(ip3))
            
            ip4 = int(self.ip_4.text())
            self.ip_4.setText(str(ip4))

            client_ip = f"{ip1}.{ip2}.{ip3}.{ip4}"

            if (0 <= ip1 <= 255) and (0 <= ip2 <= 255) and (0 <= ip3 <= 255) and (0 <= ip4 <= 255) and (client_ip not in self.clients):
                self.clients.append(client_ip)
                
                if self.users_window is not None:
                    self.users_window.update_lists(self.clients)
                
                self.update_clients_number()
            
        except ValueError:
            return

    def remove_client(self, client_index):
        if client_index < len(self.clients):
            self.clients.pop(client_index)
            self.users_window.update_lists(self.clients)
        else:
            log(f"[ERROR GUI {inspect.currentframe().f_code.co_name}]: indice fuera de rango")
        self.update_clients_number()

    def set_user_button_icon(self,status):     
        on_icon = QIcon(client_button_img_url)
        off_icon = QIcon(client_button_disable_img_url)   
        
        if status==0:
            self.client_button.setIcon(on_icon)
        elif status==1:
            self.client_button.setIcon(off_icon)

##############################################
##---------------- QOBJECTS ----------------##
##############################################

class SignalObject(QObject):
    valueChanged = pyqtSignal()

##############################################
##---------------- STYLES ------------------##
##############################################

offline_button_style = """
QPushButton {
    background-color: transparent;
    color: #9a0d0d;
    border: none;
    border-radius: 2px;
    text-align: right;
    padding: 0px 0px 0px 4px;
}

QPushButton:hover {
    background-color: transparent;
    color: #B60F0F;
}

QPushButton:pressed {
    background-color: transparent;
    color: #AAAAAA;
    border-style: inset;
}

QPushButton:disabled {
    color: rgba(132,11,11,50%);
}
"""

connecting_button_style = """
QPushButton {
    background-color: transparent;
    color: #BCB851;
    border: none;
    border-radius: 2px;
    text-align: right;
    padding: 0px 0px 0px 4px;
}

QPushButton:hover {
    background-color: transparent;
    color: #D6D15C;
}

QPushButton:pressed {
    background-color: transparent;
    color: #AAAAAA;
    border-style: inset;
}

QPushButton:disabled {
    color: rgba(145,142,62,50%);
}
"""

online_button_style = """
QPushButton {
    background-color: transparent;
    color: #36BD74;
    border: none;
    border-radius: 2px;
    text-align: right;
    padding: 0px 0px 0px 4px;
}

QPushButton:hover {
    background-color: transparent;
    color: #3FDB86;
}

QPushButton:pressed {
    background-color: transparent;
    color: #AAAAAA;
    border-style: inset;
}

QPushButton:disabled {
    color: rgba(37,131,80,50%);
}
"""

start_button_style = """
QPushButton {
    background-color: transparent;
    color: #777777;
    border: none;
    border-radius: 2px;
    text-align: right;
    padding: 0px 0px 0px 4px;
}

QPushButton:hover {
    background-color: transparent;
    color: #999999;
}

QPushButton:pressed {
    background-color: transparent;
    color: #AAAAAA;
    border-style: inset;
}

QPushButton:disabled {
    color: rgba(70,70,70,50%);
}
"""

message_box_style="""
            QMessageBox {
                background-color: #202020;
                border-radius: 10px;
                border: 1px solid #36BD74;
            }

            QMessageBox QLabel {
                color: white;
            }

            QMessageBox QPushButton {
                background-color: #36BD74;
                color: white;
                border-radius: 5px;
                padding: 5px;
                width: 60px;
                height:10px;
            }

            QMessageBox QPushButton:hover {
                background-color: #2A8C58;
            }
        """

##############################################
##------------- EXEC FUNCTION --------------##
##############################################

def UI(server_pipe, player_pipe,ltc_pipe,mtc_pipe,main_pipe):
    try:
        mainApp = QApplication(sys.argv)
        app = GUI(server_pipe,player_pipe,ltc_pipe,mtc_pipe,main_pipe)
        mainApp.exec_()
   
    except Exception as e:
        log(f"[ERROR GUI {inspect.currentframe().f_code.co_name}]: {e}")