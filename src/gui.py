import time
import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog,QMessageBox,QComboBox
from PyQt5 import uic, QtCore,QtWidgets
from PyQt5.QtCore import QRunnable, pyqtSlot, QThreadPool
from PyQt5.QtCore import Qt
from socket import *
import numpy as np
import soundfile as sf
import sounddevice as sd
import os
import datetime
from pydub import AudioSegment
from tools import *
from functools import partial
from get_nets import get_nets

##############################################
##------------------- GUI ------------------##
##############################################

class GUI(QMainWindow):

    def __init__(self,network_pipe,player_pipe,ltc_pipe,mtc_pipe):#TEST
        super(GUI,self).__init__()
        uic.loadUi("gui.ui",self)
        self.setWindowTitle("TEST")
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)  
        self.var_init()
        self.thread_pipes_init(network_pipe,player_pipe,ltc_pipe,mtc_pipe)
        self.func_init()
        self.visual_init()
        self.show()

    # ---------------- INIT CONFIG

    def var_init(self): #TEST
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
        self.audio_total_duration = 0
        
        # -- SERVER VARS
        # SERVER SEND
        self.nets = get_nets()
        self.host = "192.168.0.9"
        self.port = 44444
        self.network_is_on = False
        self.timecode = 0
        self.mode = "master"
        # SERVER RECV
        self.online = False
        self.server_error = None
        self.clients = []
        
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

    def thread_pipes_init(self,network_pipe,player_pipe,ltc_pipe,mtc_pipe):#TEST
        self.server_pipe = network_pipe
        self.player_pipe = player_pipe
        self.ltc_pipe = ltc_pipe
        self.mtc_pipe = mtc_pipe
        self.com_enable = True
        self.recv_server_thread = GUI_Recv(self.recv_server_data)
        self.recv_player_thread = GUI_Recv(self.recv_player_data)
        self.send_thread = GUI_Recv(self.send_data_to_process)
        self.recv_server_pool = QThreadPool()
        self.recv_player_pool = QThreadPool()
        self.send_pool = QThreadPool()
        self.recv_server_pool.start(self.recv_server_thread)
        self.recv_player_pool.start(self.recv_player_thread)
        self.send_pool.start(self.send_thread)

    def func_init(self): #TEST
        # WINDOW BUTTONS ASSING
        self.app_mini_button.clicked.connect(self.showMinimized)
        self.app_close_button.clicked.connect(self.close_app)
        self.main_frame_2.mouseMoveEvent = self.mouseMoveWindow
        
        # NETWORK AND MODE BUTTONS ASSING
        self.master_button.clicked.connect(self.set_master_mode)
        self.slave_button.clicked.connect(self.set_slave_mode)
        self.connect_button.clicked.connect(self.set_network)
        self.ip_combo_box.currentIndexChanged.connect(self.set_ip)

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
            self.set_ip()
        if self.nets != {}:
            nets = [f"{value} - {key}" for key, value in self.nets.items()]
            self.ip_combo_box.clear()
            self.ip_combo_box.addItems(nets)
            self.ip_combo_box.setCurrentIndex(0)
        self.audio_slider.setValue(int(self.gain*100))
        self.error_label.setVisible(False)
        self.users_icon.setVisible(False)
        self.users_label.setVisible(False)
        self.recv_mtc_data()
        
        if self.ip_combo_box.currentText() == "Networks not found": 
            self.connect_button.setEnabled(False)

    # ---------------- WINDOW CONFIG

    def mousePressEvent(self, event):#
        self.oldPosition = event.globalPos()

    def mouseMoveWindow(self, event):#
        if not self.isMaximized():
            delta = QtCore.QPoint(event.globalPos() - self.oldPosition)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPosition = event.globalPos()

    def close_app(self): #TEST
        self.com_enable = False
        self.close()

    # ---------------- BUTTONS FUNCTIONS

    # NETWORK AND MODE BUTTONS FUNCTIONS

    def set_master_mode(self): #TEST
        self.master_button.setChecked(True)
        self.slave_button.setChecked(False)
            
        if self.mode == "master":
            return
        
        self.mode = "master"
        self.timecode = 0
        if self.is_playing:
            pass
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
        self.audio_open_button.setText("Open An Audio File")
        
        if self.network_is_on:
            self.set_network()
        else:
            self.connect_button.setText("START SERVER")

        self.ltc_pipe.send({"is_playing":False})
        self.mtc_pipe.send({"is_playing":False})
        
    def set_slave_mode(self): #TEST
        self.master_button.setChecked(False)
        self.slave_button.setChecked(True)
        
        if self.mode == "slave":
            return
        
        self.mode="slave"
        self.tc = "00:00:00:00"
        
        if self.is_playing:
            pass
            self.stop()

        self.play_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.clock_button.setEnabled(False)
        self.forward_button.setEnabled(False)
        self.backward_button.setEnabled(False)
        self.audio_open_button.setEnabled(False)
        self.audio_close_button.setEnabled(False)
        self.audio_slider.setEnabled(False)
        self.audio_output_combo_box.setEnabled(False)
        self.audio_open_button.setText("Audio Player Is Disable In Slave Mode")
        self.users_icon.setVisible(False)
        self.users_label.setVisible(False)
        
        if self.network_is_on:
            self.set_network()
        else:
            self.connect_button.setText("CONNECT")
        
        self.ltc_pipe.send({"is_playing":True})
        self.mtc_pipe.send({"is_playing":True})

    def set_network(self): #TEST
        self.network_is_on = not self.network_is_on
        
        if not self.network_is_on:
            if self.mode == "master":
                self.connect_button.setText("START SERVER")
            elif self.mode == "slave":
                self.connect_button.setText("CONNECT")
            #self.connect_button.setStyleSheet(start_button_style)
            self.users_icon.setVisible(False)
            self.users_label.setVisible(False)
            self.error_label.setVisible(False)
            self.ip_combo_box.setEnabled(True)
            
        else:
            
            if not self.online and self.server_error is None:
                self.connect_button.setText("CONNECTING")
                #self.connect_button.setStyleSheet(connecting_button_style)
                #self.users_icon.setVisible(False)
                #self.users_label.setVisible(False)
                self.ip_combo_box.setEnabled(False)
                self.error_label.setVisible(False)
                self.error_label.setText(self.server_error) 

    def set_ip(self):
        if self.nets:
            net = self.ip_combo_box.currentText()
            ip = net.split(" - ")[0]
            self.host=ip

    # CONTROLS BUTTONS FUNCTIONS

    def play_pause(self): #TEST
        self.is_playing = not self.is_playing
    
        if self.is_playing:
            if self.is_paused:
                self.time_start = time.time() - self.timecode
                self.is_paused = None
            elif not self.is_paused:
                self.time_start = time.time()   
        else:
            self.paused_sample = self.current_sample
            self.is_paused = True

    def stop(self): #TEST
        self.is_playing = False
        self.is_paused = None
        self.paused_sample = 0
        self.play_button.setChecked(False)
        self.timecode = 0
        self.update_tc_labels()

    def tc_clock(self): #TEST
        if self.audio_data is None:
            fecha_actual = datetime.datetime.now()
            fecha_medianoche = fecha_actual.replace(hour=0, minute=0, second=0, microsecond=0)
            diferencia = fecha_actual - fecha_medianoche
            segundos_transcurridos = diferencia.total_seconds()
            if self.is_playing:
                self.time_start = time.time()-segundos_transcurridos
            else:
                self.time_start = time.time()-segundos_transcurridos
                self.is_playing = True
                self.play_button.setChecked(True)

    def forward(self): #TEST
        if self.audio_data is not None: #WITH FILE TRACK
            
            posible_sample = int((10 + self.timecode) * self.sample_rate)
            if posible_sample < len(self.audio_data):
                self.paused_sample = posible_sample
                self.timecode = self.timecode + 10
            else:
                self.paused_sample = 0
                self.timecode = self.audio_total_duration
                if self.is_playing:
                    self.is_playing = False
                    self.play_button.setChecked(False)
            self.update_tc_labels()
            
            if not self.is_playing:
                self.paused_sample = self.current_sample

        elif self.audio_data is None: #WITHOUT FILE TRACK
            
            posible_time_start = (time.time()  - (self.timecode + 10)) 
            
            if self.is_playing:
                
                if (time.time() - posible_time_start) < 86400:
                    self.time_start = self.time_start - 10
                else:
                    self.stop()
                    self.timecode = 86400
                    self.update_tc_labels()
                    
            elif not self.is_playing:
                
                if (time.time() - posible_time_start) < 86400:
                    self.time_start = posible_time_start
                    self.paused_time =  time.time()
                    self.timecode = self.timecode + 10
                    
                else:
                    self.paused_time = None
                    self.timecode = 86400
                self.update_tc_labels()

    def backward(self): #TEST
        if self.audio_data is not None: #WITH FILE TRACK
            
            posible_sample=max(0,(self.current_sample  - (self.sample_rate*10)))
            if posible_sample > 0:
                self.paused_sample =  posible_sample
                self.timecode = self.timecode -10
            else:
                self.paused_sample = 0
                self.timecode = 0
            self.update_tc_labels() 
            
            if not self.is_playing:
                self.paused_sample = self.current_sample
                
        elif self.audio_data is None: #WITHOUT FILE TRACK
            
            posible_time_start = (time.time()  - (self.timecode - 10)) 
            
            if self.is_playing:

                if (time.time() - posible_time_start) > 0:
                    self.time_start = self.time_start + 10
                    print("#")
                else:
                    self.stop()
                    self.timecode = 0
                    self.update_tc_labels()
                    
            elif not self.is_playing:

                if (time.time() - posible_time_start) > 0:
                    self.time_start = posible_time_start
                    self.paused_time =  time.time()
                    self.timecode = self.timecode - 10
                    
                else:
                    self.paused_time = None
                    self.timecode = 0
                self.update_tc_labels()

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
            self.ip_combo_box.setEnabled(False)
            self.master_button.setEnabled(False)
            self.slave_button.setEnabled(False)
            
        else:
            self.master_button.setEnabled(True)
            self.slave_button.setEnabled(True)
            self.ltc_frame.setEnabled(True)
            self.mtc_frame.setEnabled(True)
            self.connect_button.setEnabled(True)
            self.ip_combo_box.setEnabled(True)
            
            if self.mode == "master":
                self.audio_frame.setEnabled(True)
                self.play_button.setEnabled(True)
                self.stop_button.setEnabled(True)
                self.clock_button.setEnabled(True)
                self.forward_button.setEnabled(True)
                self.backward_button.setEnabled(True)
                self.audio_slider.setEnabled(True)
                self.connect_button.setEnabled(True)

        if self.ip_combo_box.currentText() == "Networks not found": 
            self.connect_button.setEnabled(False)

    # PLAYER BUTTONS FUNCTIONS

    def open_audio_file(self): #TEST
        try:
            file_path, _ = QFileDialog.getOpenFileName(None, 'Abrir archivo de audio', '', 'Archivos de audio (*.wav *.mp3)')

            if self.is_playing:
                self.stop()

            if file_path:
                _, file_extension = os.path.splitext(file_path)
                file_extension = file_extension.lower()

                if file_extension == '.wav':
                    audio_data, sample_rate = sf.read(file_path)
                elif file_extension == '.mp3':
                    audio = AudioSegment.from_mp3(file_path)
                    audio.export('temp.wav', format='wav')
                    audio_data, sample_rate = sf.read('temp.wav')
                    os.remove('temp.wav')
                else:
                    raise ValueError('Formato de archivo no válido.')

                self.audio_total_duration = len(audio_data) / sample_rate
                self.audio_data = audio_data
                self.sample_rate = sample_rate

                file_name = os.path.basename(file_path)
                self.audio_open_button.setText(file_name.upper())

                self.remaining_time = self.audio_total_duration

        except Exception as e:
            print('[OPEN AUDIO ERROR]:', str(e))
            self.close_audio_file()

    def close_audio_file(self): #TEST
        if self.audio_data is not None:
            if self.is_playing:
                message_box = QMessageBox(self)
                message_box.setWindowTitle("Warning")
                message_box.setText("Audio is playing!")
                message_box.setInformativeText("Do you want to close the audio file?")
                message_box.setIcon(QMessageBox.Question)
                message_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                wrapper = partial(self.center_widget, message_box)
                QtCore.QTimer.singleShot(0, wrapper)
                #message_box.setStyleSheet(message_box_style)
                message_box.setWindowFlags(message_box.windowFlags() | Qt.FramelessWindowHint)
                reply = message_box.exec_()

                if reply == QMessageBox.No:
                    return
                
            self.stop()        
            self.audio_data = None
            self.sample_rate = None
            self.stream = None
            self.audio_open_button.setText("OPEN AN AUDIO FILE TO PLAY")
            self.timecode = 0
            self.update_tc_labels()

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
            self.ltc_tc_label.setText(secs_to_tc(self.mtc_offset + self.timecode,self.mtc_fps))
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

    def update_tc_labels(self): #TEST
        self.tc_label.setText(str(secs_to_tc(self.timecode)))
            
            
        if self.audio_data is None:
            self.remaning_tc.setText(str(secs_to_tc(86400-self.timecode)))
        else:
            self.remaning_tc.setText(str(secs_to_tc(self.audio_total_duration-self.timecode)))
            
        if self.ltc_is_on:
            self.ltc_tc_label.setText(str(secs_to_tc(self.timecode + self.ltc_offset,self.ltc_fps)))
        if self.mtc_is_on:
            self.mtc_tc_label.setText(str(secs_to_tc(self.timecode + self.mtc_offset,self.mtc_fps)))

    # ---------------- THREAD FUNCTIONS (PIPES COMUNICATION)

    def send_data_to_process(self): #THREAD
        
        # SEND CONFIRMATIONS
        self.last_is_playing = self.is_playing
        self.last_time_start = self.time_start
        self.last_audio_data = self.audio_data
        self.last_sample_rate = self.sample_rate
        self.last_audio_device = self.audio_device
        self.last_gain = self.gain
        self.last_paused_sample = self.paused_sample
        
        self.last_host = self.host
        self.last_port = self.port
        self.last_network_is_on = self.network_is_on
        self.last_timecode = self.timecode
        self.last_mode = self.mode
        
        self.last_ltc_output_device = self.ltc_output_device
        self.last_ltc_fps = self.ltc_fps
        self.last_ltc_offset = self.ltc_offset
        self.last_ltc_is_on = self.ltc_is_on
        
        self.last_mtc_output_device = self.mtc_output_device
        self.last_mtc_fps = self.mtc_fps
        self.last_mtc_offset = self.mtc_offset
        self.last_mtc_is_on = self.mtc_is_on
        
        while self.com_enable:
            data_to_send = {}
            if self.last_is_playing != self.is_playing:
                data_to_send['is_playing'] = self.is_playing
                if self.mode == "master":
                    self.player_pipe.send(data_to_send)
                self.ltc_pipe.send(data_to_send)
                self.mtc_pipe.send(data_to_send)            
                self.last_is_playing = self.is_playing
                
            if self.last_time_start != self.time_start:
                data_to_send['time_start'] = self.time_start
                self.player_pipe.send(data_to_send)    
                self.last_time_start = self.time_start
                
            if not np.array_equal(self.last_audio_data, self.audio_data):
                data_to_send['audio_data'] = self.audio_data
                self.player_pipe.send(data_to_send)       
                self.last_audio_data = self.audio_data
                
            if self.last_sample_rate != self.sample_rate:
                data_to_send['sample_rate'] = self.sample_rate
                self.player_pipe.send(data_to_send)        
                self.last_sample_rate = self.sample_rate
            
            if self.last_audio_device != self.audio_device:
                data_to_send['audio_device'] = self.audio_device
                self.player_pipe.send(data_to_send)        
                self.last_audio_device = self.audio_device        
            
            if self.last_gain != self.gain:
                data_to_send['gain'] = self.gain
                self.player_pipe.send(data_to_send)          
                self.last_gain = self.gain        

            if self.last_paused_sample != self.paused_sample:
                data_to_send['paused_sample'] = self.paused_sample
                self.player_pipe.send(data_to_send)         
                self.last_paused_sample = self.paused_sample
            
            if self.last_host != self.host:
                data_to_send['host'] = self.host
                self.server_pipe.send(data_to_send)        
                self.last_host = self.host
                
            if self.last_port != self.port:
                data_to_send['port'] = self.port
                self.server_pipe.send(data_to_send)         
                self.last_port = self.port
                
            if self.last_network_is_on != self.network_is_on:
                data_to_send['network_is_on'] = self.network_is_on
                self.server_pipe.send(data_to_send)        
                self.last_network_is_on = self.network_is_on
                
            if self.last_timecode != self.timecode:
                data_to_send['tc'] = self.timecode
                if self.mode=="master":
                    self.server_pipe.send(data_to_send)
                self.ltc_pipe.send(data_to_send)
                self.mtc_pipe.send(data_to_send)         
                self.last_timecode = self.timecode
            
            if self.last_mode != self.mode:
                data_to_send['mode'] = self.mode
                self.server_pipe.send(data_to_send)         
                self.last_mode = self.mode   
            
            if self.last_ltc_is_on != self.ltc_is_on:
                data_to_send['ltc_is_on'] = self.ltc_is_on
                self.ltc_pipe.send(data_to_send)          
                self.last_ltc_is_on = self.ltc_is_on  
                
            if self.last_ltc_output_device != self.ltc_output_device:
                data_to_send['ltc_output_device'] = self.ltc_output_device
                self.ltc_pipe.send(data_to_send)           
                self.last_ltc_output_device = self.ltc_output_device
                
            if self.last_ltc_fps != self.ltc_fps:
                data_to_send['ltc_fps'] = self.ltc_fps
                self.ltc_pipe.send(data_to_send)   
                self.last_ltc_fps = self.ltc_fps
                
            if self.last_ltc_offset != self.ltc_offset:
                data_to_send['ltc_offset'] = self.ltc_offset
                self.ltc_pipe.send(data_to_send)   
                self.last_ltc_offset = self.ltc_offset
                
            if self.last_mtc_is_on != self.mtc_is_on:
                data_to_send['mtc_is_on'] = self.mtc_is_on
                self.mtc_pipe.send(data_to_send)           
                self.last_mtc_is_on = self.mtc_is_on  
                
            if self.last_mtc_output_device != self.mtc_output_device:
                data_to_send['mtc_output_device'] = self.mtc_output_device
                self.mtc_pipe.send(data_to_send)           
                self.last_mtc_output_device = self.mtc_output_device
                
            if self.last_mtc_fps != self.mtc_fps:
                data_to_send['mtc_fps'] = self.mtc_fps
                self.mtc_pipe.send(data_to_send)   
                self.last_mtc_fps = self.mtc_fps
                
            if self.last_mtc_offset != self.mtc_offset:
                data_to_send['mtc_offset'] = self.mtc_offset
                self.mtc_pipe.send(data_to_send)   
                self.last_mtc_offset = self.mtc_offset
                
            time.sleep(0.01)

    def recv_server_data(self): #THREAD
        last_timecode = self.timecode
        while self.com_enable:
            
            network_recv_data = self.server_pipe.recv()

            if 'online' in network_recv_data:
                self.online = network_recv_data["online"]
            if 'error' in network_recv_data:
                self.server_error = network_recv_data["error"]
            if 'clients' in network_recv_data:
                self.clients = network_recv_data["clients"]   
            if 'timecode_recv' in network_recv_data and self.mode == "slave":
                self.timecode = network_recv_data["timecode_recv"]     

            if last_timecode != self.timecode and self.mode == "slave":
                last_timecode = self.timecode
                self.update_tc_labels()
                
            if self.online and self.network_is_on:
                if self.mode=="master":
                    self.connect_button.setText("SENDING")
                elif self.mode=="slave":
                    self.connect_button.setText("LISTENING")
                #self.connect_button.setStyleSheet(online_button_style)
                #if self.mode=="master":
                #    self.users_icon.setVisible(True)
                #    self.users_label.setVisible(True)
                self.users_label.setText(str(len(self.clients)))
                self.error_label.setVisible(False)
                self.error_label.setText(self.server_error)
                
            elif self.network_is_on:
                self.connect_button.setText("ERROR")
                #self.connect_button.setStyleSheet(offline_button_style)
                #self.users_icon.setVisible(False)
                #self.users_label.setVisible(False)
                self.error_label.setVisible(True)
                self.error_label.setText(self.server_error)

    def recv_player_data(self): #THREAD
        last_timecode = self.timecode
        while self.com_enable:
            
            player_recv_data = self.player_pipe.recv()
            
            if 'tc' in player_recv_data and self.mode == "master":
                self.timecode = player_recv_data["tc"]
            if 'current_sample' in player_recv_data:
                self.current_sample = player_recv_data["current_sample"]   
            
            if last_timecode != self.timecode and self.mode == "master":
                last_timecode = self.timecode
                self.update_tc_labels()

    def recv_ltc_data(self): #THREAD
        recive_data = self.mtc_pipe.recv()
        
        if 'ltc_devices' in recive_data:
            self.ltc_outputs = recive_data["ltc_devices"]
            if self.ltc_outputs != {}:
                self.ltc_output_combo_box.clear()
                self.ltc_output_combo_box.addItems(list(self.ltc_outputs.values()))

    def recv_mtc_data(self): #THREAD
        recive_data = self.mtc_pipe.recv()
        
        if 'mtc_devices' in recive_data:
            self.mtc_outputs = recive_data["mtc_devices"]
            if self.mtc_outputs != {}:
                self.mtc_output_combo_box.clear()
                self.mtc_output_combo_box.addItems(list(self.mtc_outputs.values()))

##############################################
##---------------- THREAD ------------------##
##############################################

class GUI_Recv(QRunnable):
    
    def __init__(self, InFunc):
        super(GUI_Recv, self).__init__()
        self.Func = InFunc

    @pyqtSlot(name="1")
    def run(self): #TEST
        self.Func()

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
    color: #999999;
}

QPushButton:pressed {
    background-color: transparent;
    color: #AAAAAA;
    border-style: inset;
}

QPushButton:disabled {
    color: #606060;
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
    color: #999999;
}

QPushButton:pressed {
    background-color: transparent;
    color: #AAAAAA;
    border-style: inset;
}

QPushButton:disabled {
    color: #606060;
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
    color: #999999;
}

QPushButton:pressed {
    background-color: transparent;
    color: #AAAAAA;
    border-style: inset;
}

QPushButton:disabled {
    color: #606060;
}
"""

start_button_style = """
QPushButton {
    background-color: transparent;
    color: #707070;
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
    color: #606060;
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

def UI(server_pipe, player_pipe,ltc_pipe,mtc_pipe):
    mainApp = QApplication(sys.argv)
    app = GUI(server_pipe,player_pipe,ltc_pipe,mtc_pipe)
    mainApp.exec_()   