from PyQt5 import uic, QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from functools import partial
from PyQt5 import QtCore, QtWidgets
from socket import *
import sys
from logs_tools import *
import time
import numpy as np
import soundfile as sf
import sounddevice as sd
import os
import datetime
from pydub import AudioSegment
import socket
import netifaces as ni
from threading import Thread, current_thread, Event

class Worker(QRunnable):
    def __init__(self, InFunc):
        super(Worker, self).__init__()
        self.Func = InFunc

    @pyqtSlot(name="1")
    def run(self):
        self.Func()

class Worker2(QRunnable):
    def __init__(self, InFunc):
        super(Worker2, self).__init__()
        self.Func = InFunc

    @pyqtSlot(name="2")
    def run(self):
        self.Func()




class Master_UI(QMainWindow):
    
    def __init__(self):
        super(Master_UI, self).__init__()
        uic.loadUi("master.ui", self)
        self.setWindowTitle("SDM Timecode")
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)        
        self.init_variables()
    
    # --------------------MAIN FUNCTIONS------------------------
    
    def init_variables(self):#OK
        self.play_process = Worker(self.player)
        self.server_process = Worker2(self.start_server)
        
        
        self.is_first_time = True
        self.play_process_run = True
        self.server_process_run = True
        
        self.is_pin = False
        self.is_lock = False
        
        self.network_status = False
        
        self.ips=self.get_aviable_networks()
        if self.ips != []:
            self.ip_combo_box.clear()
            self.ip_combo_box.addItems(self.ips)
        
        self.host = "127.0.0.1"
        self.port = 12345   
        self.direccion = f"{self.host}:{self.port}"
        self.online = False
        self.s = None
        self.clientes_conectados = []
        
        self.is_playing = False
        self.audio_data = None
        self.sample_rate = None
        self.stream = None
        self.audio_device = sd.default.device
        self.audio_devices = self.get_output_devices()
        if self.audio_devices != {}:
            self.audio_output_combo_box.clear()
            self.audio_output_combo_box.addItems(list(self.audio_devices.values()))
        self.current_sample = 0
        self.audio_paused_sample = 0
        self.audio_total_duration = 0
        self.gain=0.8
        self.audio_slider.setValue(int(self.gain*100))
        self.paused_time = None
        
        self.fps = 99
        self.start_time = 0
        self.end_time = 86400
        self.elapsed_time = self.start_time
        self.remaining_time = self.end_time
        self.time_now = self.start_time
        self.timecode = self.start_time
        self.time_start = 0
        
        self.server_error_label.setVisible(False)
        self.users_label.setVisible(False)
        
        # --------------------- FUNCTION ASSING--------------------------
        # WINDOW ASSING
        self.app_mini_button.clicked.connect(self.showMinimized)
        self.app_close_button.clicked.connect(self.close_app)
        self.main_frame_2.mouseMoveEvent = self.mouseMoveWindow

        # NETWORK
        self.connect_button.clicked.connect(self.set_network)

        # CONTROL BUTTONS ASSING
        self.play_button.clicked.connect(self.play_pause)
        self.stop_button.clicked.connect(self.stop)
        self.clock_button.clicked.connect(self.tc_clock)
        self.forward_button.clicked.connect(self.forward)
        self.backward_button.clicked.connect(self.backward)
        self.pin_button.clicked.connect(self.always_on_top)
        self.lock_button.clicked.connect(self.lock)
        
        # CONTROL BUTTONS ASSING
        self.audio_open_button.clicked.connect(self.open_audio_file)
        self.audio_close_button.clicked.connect(self.close_audio_file)
        self.audio_slider.valueChanged.connect(self.set_gain)
        self.audio_output_combo_box.currentIndexChanged.connect(self.set_audio_device)
        
        # TIME FUNCTIONS ASING
        self.set_start_button.clicked.connect(self.set_start_time)
        self.set_end_button.clicked.connect(self.set_end_time)
        
        self.show()
        self.update_times()

    def mousePressEvent(self, event):  # OK
        self.oldPosition = event.globalPos()

    def mouseMoveWindow(self, event):  # OK
        if not self.isMaximized():
            delta = QtCore.QPoint(event.globalPos() - self.oldPosition)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPosition = event.globalPos()

    def close_app(self):#OK
        self.play_process_run = False
        self.close()
    #D9AF56
    # -------------------BUTTONS FUCNTIONS----------------------

    def play_pause(self):#OK
        self.is_playing = not self.is_playing
        self.time_now = self.start_time
        
        if self.is_playing and self.is_first_time:
            self.is_first_time = False
            self.playerPool = QThreadPool()
            self.playerPool.start(self.play_process)
            
        if self.is_playing:
            if self.paused_time is not None:
                self.time_start = time.time() - self.paused_time
                self.paused_time = None
            elif self.paused_time is None:
                self.time_start = time.time()
                
            if self.audio_paused_sample !=0:
                self.current_sample = self.audio_paused_sample
            elif self.paused_time == 0:
                self.current_sample = 0
        
        else:
            self.audio_paused_sample = self.current_sample
            self.paused_time = time.time() - self.time_start

    def stop(self):#OK
        self.is_playing = False
        self.paused_time = None
        self.audio_paused_sample = 0
        self.current_sample = 0
        self.play_button.setChecked(False)
        self.timecode = self.start_time
        self.update_times()

    def tc_clock(self):#OK
        fecha_actual = datetime.datetime.now()
        fecha_medianoche = fecha_actual.replace(hour=0, minute=0, second=0, microsecond=0)
        diferencia = fecha_actual - fecha_medianoche
        segundos_transcurridos = diferencia.total_seconds()
            
        if self.audio_data is None:
            if self.is_playing:
                self.time_start = time.time()-segundos_transcurridos + self.start_time
            else:
                self.time_start = time.time()-segundos_transcurridos + self.start_time
                self.is_playing = True
                self.play_button.setChecked(True)
                if self.is_playing and self.is_first_time:
                    self.is_first_time = False
                    self.playerPool = QThreadPool()
                    self.playerPool.start(self.play_process)

    def forward(self):#OK
        if self.audio_data is not None: #WITH FILE TRACK
            
            posible_sample = int((10 + self.timecode) * self.sample_rate)
            if posible_sample < len(self.audio_data):
                self.current_sample = posible_sample
                self.timecode = self.timecode + 10
            else:
                self.current_sample = 0
                self.timecode = self.audio_total_duration
                if self.is_playing:
                    self.is_playing = False
                    self.play_button.setChecked(False)
            self.update_times()
            
            if not self.is_playing:
                self.audio_paused_sample = self.current_sample

        elif self.audio_data is None: #WITHOUT FILE TRACK
            
            if self.is_playing:
                if (time.time() - (self.time_start - 10)) < self.end_time:
                    self.time_start = self.time_start - 10
                else:
                    self.time_start = min(time.time() - self.end_time,time.time() + self.end_time)
                    
            elif not self.is_playing:
                
                posible_time = (time.time()  - (self.timecode + 10)) 
                if (time.time() - posible_time) < self.end_time:
                    self.time_start = posible_time
                    self.paused_time =  (time.time() - self.time_start) - self.start_time
                    self.timecode = self.timecode + 10
                else:
                    self.paused_time = None
                    self.timecode = self.end_time
                self.update_times()

    def backward(self):#OK
        if self.audio_data is not None: #WITH FILE TRACK
            
            posible_sample=max(0,(self.current_sample  - (self.sample_rate*10)))
            if posible_sample > 0:
                self.current_sample =  posible_sample
                self.timecode = self.timecode -10
            else:
                self.current_sample = 0
                self.timecode = 0
            self.update_times() 
            
            if not self.is_playing:
                self.audio_paused_sample = self.current_sample
                
        elif self.audio_data is None: #WITHOUT FILE TRACK
            
            if self.is_playing:
                
                if (time.time() - (self.time_start + 10)) > self.start_time:
                    self.time_start = self.time_start + 10
                else:
                    self.time_start = max(time.time() + self.start_time,time.time() - self.start_time)
                    
            elif not self.is_playing:
                
                posible_time = (time.time()  - (self.timecode - 10)) 
                if (time.time() - posible_time) > self.start_time:
                    self.time_start = posible_time
                    self.paused_time =  (time.time() - self.time_start) - self.start_time
                    self.timecode = self.timecode - 10
                    
                else:
                    self.paused_time = None
                    self.timecode = self.start_time
                self.update_times()

    def always_on_top(self):#OK
        self.is_pin= not self.is_pin
        if self.windowFlags() & Qt.WindowStaysOnTopHint:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.show() 

    def lock(self):#OK
        self.is_lock = not self.is_lock
        if self.is_lock:
            self.audio_frame.setEnabled(False)
            self.audio_output_combo_box.setEnabled(False)
            self.play_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.clock_button.setEnabled(False)
            self.forward_button.setEnabled(False)
            self.backward_button.setEnabled(False)
            self.audio_slider.setEnabled(False)
            self.connect_button.setEnabled(False)
            self.ip_combo_box.setEnabled(False)
            self.time_frame.setEnabled(False)
        else:
            self.audio_frame.setEnabled(True)
            self.audio_output_combo_box.setEnabled(True)
            self.play_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.clock_button.setEnabled(True)
            self.forward_button.setEnabled(True)
            self.backward_button.setEnabled(True)
            self.audio_slider.setEnabled(True)
            self.connect_button.setEnabled(True)
            if not self.network_status:
                self.ip_combo_box.setEnabled(True)
            if self.audio_data is None:
                self.time_frame.setEnabled(True)

    def set_gain(self):#OK
        self.gain = self.audio_slider.value()/100

    def set_audio_device(self):#OK
        if self.is_playing:
            self.play_pause()
            time.sleep(0.01)
            self.play_pause()
        if self.audio_devices != {}:
            device_name = self.audio_output_combo_box.currentText()
            for key, value in self.audio_devices.items():
                if value == device_name:
                    device_index = key
                    break
            self.audio_device = device_index   

    def set_network(self):#EMPTY
        self.network_status = not self.network_status
        if self.network_status:
            self.server_process_run=True
            self.host = self.ip_combo_box.currentText()
            self.port = 12345   
            self.direccion = f"{self.host}:{self.port}"
            self.ip_combo_box.setEnabled(False)
            self.serverPool = QThreadPool()
            self.serverPool.start(self.server_process)
        else:
            self.stop_server()
            self.ip_combo_box.setEnabled(True)

    def set_start_time(self):#OK
        
        def errase_values():
            self.hh_start.setText("")
            self.mm_start.setText("")
            self.ss_start.setText("")
            self.ff_start.setText("")     
               
        time_entries = [self.hh_start.text(), self.mm_start.text(),self.ss_start.text(),self.ff_start.text()]
        time_values = []
        
        for entry in time_entries:
            time_str = entry or "0"
            if not time_str.isdigit():
                errase_values()
                return
            time_values.append(int(time_str))
        
        hh, mm, ss, ff = time_values
        
        if hh > 23 or mm > 59 or ss > 59 or ff > self.fps:
            errase_values()
            return

        new_time = f"{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}"
        new_time_in_seconds=self.timecode_to_seconds(new_time,self.fps)
        
        if new_time_in_seconds > self.end_time:
            errase_values()
            return
        
        self.start_time = new_time_in_seconds
        errase_values()
        self.stop()

    def set_end_time(self):#OK
        
        def errase_values():
            self.hh_end.setText("")
            self.mm_end.setText("")
            self.ss_end.setText("")
            self.ff_end.setText("")     
               
        time_entries = [self.hh_end.text(), self.mm_end.text(),self.ss_end.text(),self.ff_end.text()]
        time_values = []
        
        for entry in time_entries:
            time_str = entry or "0"
            if not time_str.isdigit():
                errase_values()
                return
            time_values.append(int(time_str))
        
        hh, mm, ss, ff = time_values
        
        if hh > 23 or mm > 59 or ss > 59 or ff > self.fps:
            errase_values()
            return

        new_time = f"{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}"
        new_time_in_seconds=self.timecode_to_seconds(new_time,self.fps)
        
        if new_time_in_seconds < self.start_time:
            errase_values()
            return
        elif new_time_in_seconds == 0:
            self.end_time = 86400
        else:
            self.end_time = new_time_in_seconds
            
        errase_values()
        self.stop()

    #D9AF56
    # --------------------LOGIC FUCNTIONS-----------------------

    def player(self):#OK
        while self.play_process_run:
            if self.is_playing:
                if self.sample_rate != None:
                    self.play_audio()
                else:
                    self.play_tc()
            time.sleep(0.1)

    def play_tc(self):#OK
        while self.time_now < self.end_time and self.is_playing:
            self.time_now = (time.time() - self.time_start) + self.start_time
            self.timecode = self.time_now
            self.update_times()
            time.sleep(1 / self.fps)
        self.is_playing = False
        self.play_button.setChecked(False)

    def play_audio(self):#OK
        self.stream = sd.OutputStream(
            callback=self.audio_callback,
            channels=self.audio_data.shape[1],
            samplerate=self.sample_rate,
            device=self.audio_device,
        )

        with self.stream:
            while self.is_playing and self.current_sample < len(self.audio_data) :
                time.sleep(0.01)  # Pequeña pausa para evitar bloquear la CPU
            self.is_playing = False
            self.play_button.setChecked(False)

    def audio_callback(self, outdata, ff, time, status):#OK
        if self.is_playing:
            if self.current_sample < len(self.audio_data):
                outdata[:ff, :] = np.resize(
                    self.audio_data[self.current_sample : self.current_sample + ff, :],
                    (ff, 2),
                ) * self.gain
                self.current_sample += ff
                segundo_actual = (self.current_sample / self.sample_rate ) - (2/self.fps)
                self.timecode = segundo_actual
                self.update_times()
        else:
            outdata[:ff, :] = np.resize(
                    0,
                    (ff, 2),
                ) * 0

    def open_audio_file(self):#OK
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
                self.time_frame.setEnabled(False)

                self.start_time = 0
                self.elapsed_time = 0
                self.end_time = self.audio_total_duration
                self.remaining_time = self.audio_total_duration
                self.update_times()

        except Exception as e:
            print('[OPEN AUDIO ERROR]:', str(e))
            self.close_audio_file()

    def close_audio_file(self):#OK
        if self.audio_data is not None:
            if self.is_playing:
                message_box = QMessageBox(self)
                message_box.setWindowTitle("Advertencia")
                message_box.setText("¿Estás seguro de cerrar el archivo de audio?")
                message_box.setIcon(QMessageBox.Warning)
                message_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                wrapper = partial(self.center, message_box)
                QtCore.QTimer.singleShot(0, wrapper)
                self.set_message_box_style(message_box)
                message_box.setWindowFlags(message_box.windowFlags() | Qt.FramelessWindowHint)
                reply = message_box.exec_()

                if reply == QMessageBox.No:
                    return
                
            self.stop()        
            self.audio_data = None
            self.sample_rate = None
            self.stream = None
            self.audio_open_button.setText("OPEN AN AUDIO FILE TO PLAY")
            self.time_frame.setEnabled(True)
            
            self.start_time = 0
            self.elapsed_time = 0
            self.end_time = 86400
            self.remaining_time = self.end_time - self.start_time
            self.update_times()           

    # --------------------UPDATE FUCNTIONS-----------------------
    
    def timecode_to_seconds(self, timecode, fps):#OK
        horas, minutos, segundos, frames = map(int, timecode.split(":"))
        total_seconds = (horas * 3600) + (minutos * 60) + segundos + (frames / fps)
        return total_seconds

    def seconds_to_timecode(self, seconds, fps):#OK
        hh = int(seconds / 3600)
        mm = int((seconds % 3600) / 60)
        ss = int(seconds % 60)
        ff = int((seconds * fps) % fps)
        return f"{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}"
    
    def update_times(self):#OK
        self.elapsed_time = self.timecode - self.start_time
        self.remaining_time = self.end_time - self.timecode
        self.tc_label.setText(self.seconds_to_timecode(self.timecode,self.fps))
        self.start_time_label.setText(self.seconds_to_timecode(self.start_time,self.fps))
        self.end_time_label.setText(self.seconds_to_timecode(self.end_time,self.fps))
        self.elapsed_time_label.setText(self.seconds_to_timecode(self.elapsed_time,self.fps))
        self.remaining_time_label.setText(self.seconds_to_timecode(self.remaining_time,self.fps))

    def set_message_box_style(self, message_box):#OK
        message_box.setStyleSheet("""
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
        """)

    def center(self,window):#OK
        window.setGeometry(
            QtWidgets.QStyle.alignedRect(
                QtCore.Qt.LeftToRight,
                QtCore.Qt.AlignCenter,
                window.size(),
                self.geometry(),
            )
        )
        
    def get_output_devices(self):#OK
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

    def get_aviable_networks(self):#OK
        interfaces = ni.interfaces()
        ips = []

        for iface in interfaces:
            ifaddrs = ni.ifaddresses(iface)
            if socket.AF_INET in ifaddrs:
                for link in ifaddrs[socket.AF_INET]:
                    ip = link['addr']
                    if ip != '127.0.0.1':
                        ips.append(ip)

        return ips

    def start_server(self):
        if self.server_process_run:
            while not self.online:
                try:
                    self.s = socket.socket(AF_INET, SOCK_STREAM)
                    self.s.bind((self.host, self.port))
                    log(f"[SERVER START ON]: {self.direccion}", GREEN)
                    self.s.listen(5)
                    log(f"[SERVER BROADCASTING ON]: {self.direccion}", GREEN)
                    self.online = True
                    print("HOla")
                    while self.online:
                        client, address = self.s.accept()
                        log(f"[CLIENTE CONECTADO]: {address}", GREEN)
                        self.clientes_conectados.append(client)
                        self.sender_thread = Thread(
                            target=self._sender, args=(client, address)
                        )
                        self.sender_thread.start()

                except Exception as e:
                    #if e.errno == 10048:
                    #log(f"[SERVER ERROR]: Ya Existe Un Servidor Iniciado en: {self.direccion}, Reintentando...",RED,)
                    #elif e.errno == 10038:
                    #log(f"[SERVER DISCONECTED]: Stop Event", RED)
                    #else:
                    log(f"[SERVER DISCONECTED]: {e}", RED)
                    self.online = False
                    time.sleep(1)
    
    def _sender(self, conexion, address):
        last_timecode=""
        while self.online and self.server_process_run:
            if last_timecode !=self.timecode:
                try:
                    data_str = str(self.timecode)
                    conexion.send(bytes(data_str, "utf-8"))
                    last_timecode = self.timecode
                except Exception as e:
                    self.clientes_conectados.append(conexion)
                    log(f"[CLIENTE {address} DESCONECTADO]: {e}", RED)
                    break

    def stop_server(self):
        self.server_process_run = False
        self.online = False
        if self.s:
            self.s.close()
            self.s = None
        log(f"[SERVER DICONECTED]: Stop Event", RED)

if __name__ == "__main__":
    mainApp = QApplication(sys.argv)
    app = Master_UI()
    mainApp.exec_()
