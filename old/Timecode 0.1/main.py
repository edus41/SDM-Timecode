from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5 import uic, QtCore
from PyQt5.QtCore import Qt
from socket import *
import sys
from timecode import Timecode
import datetime
import time
import re
import ltc_generator as LTC
from py_audio_class import AudioDevice
from py_midi_class import MidiDevice
from logs_tools import *
from threading import Thread, current_thread,Event
import select


connected_button_stylesheet = """QPushButton {
        background-color: transparent;
        color: #9a0d0d;
        border: none;
        border-radius: 2px;
		text-align: right;
		padding:0px 0px 0px 4px;
}

QPushButton:hover {
	    background-color: transparent;
       	color: #999999;
    }

QPushButton:pressed {
        background-color: transparent;
		color:#AAAAAA;
        border-style: inset;
    }

QPushButton:disabled {
        color: #606060;
    }"""

connected_button_stylesheet2 = """QPushButton {
        background-color: transparent;
        color: #36BD74;
        border: none;
        border-radius: 2px;
		text-align: right;
		padding:0px 0px 0px 4px;
}

QPushButton:hover {
	    background-color: transparent;
       	color: #999999;
    }

QPushButton:pressed {
        background-color: transparent;
		color:#AAAAAA;
        border-style: inset;
    }

QPushButton:disabled {
        color: #606060;
    }"""
    
    
    
    
class UI(QMainWindow):
    def __init__(self):
        super(UI,self).__init__()
        uic.loadUi("gui.ui",self)
        self.setWindowTitle("SDM Timecode")
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        
        #----------------------------------------------------------------

        self.tc_thread = TC_Thread(self)
        self.tc_thread.tc_data.connect(self.get_tc_data)
        self.tc_thread.ltc_data.connect(self.get_ltc_data)
        self.tc_thread.mtc_data.connect(self.get_mtc_data)
        
        self.server_thread = Server_Thread(self)
        self.server_thread.server_data.connect(self.get_server_data)
        self.server_thread.server_error.connect(self.get_server_error)
        self.server_thread.server_clients.connect(self.get_server_clients)

        # --------------------- FUNCTION ASSING--------------------------
        # WINDOW ASSING
        self.app_mini_button.clicked.connect(self.showMinimized)
        self.app_close_button.clicked.connect(self.close_app)
        self.tc_label.mouseMoveEvent = self.mouseMoveWindow
        
        # NETWORK AND MODE ASSING
        self.master_button.clicked.connect(self.set_master_mode)
        self.slave_button.clicked.connect(self.set_slave_mode)
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
      
    def mousePressEvent(self,event):#OK
        self.oldPosition = event.globalPos()

    def mouseMoveWindow(self,event):#OK
        if not self.isMaximized():
            delta=QtCore.QPoint(event.globalPos() - self.oldPosition)
            self.move(self.x()+delta.x(),self.y()+delta.y())
            self.oldPosition = event.globalPos()

    def set_init_state(self):#EMPTY
        
        # BUTTONS / NETWORK / MODE
        self.mode = "master"
        self.network_status = False 
        self.is_playing = False
        self.is_pin = False
        self.is_lock = False
        self.host = "127.0.0.1" 
        self.port = 12345
        self.tc = '00:00:00:00'
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
        self.mtc_output_devices =  None
        
        # WIDGETS INIT
        self.users_icon_label.setVisible(False)
        self.users_label.setVisible(False)
        self.slave_button.setChecked(False)
        self.master_button.setChecked(True)
        
        # DEVICES INIT
        self.update_devices_lists()

    def close_app(self):##EMPTY
        self.close()
     
    # ------------------NETWORK AND MODE FUNCTIONS---------------------

    def set_network(self):#EMPTY
        self.network_status = not self.network_status
        self.host = f"{self.ip_1.text()}.{self.ip_2.text()}.{self.ip_3.text()}.{self.ip_4.text()}"
        ip_valida = re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', self.host) is not None
        if ip_valida:
            if self.network_status:
                self.start_server_thread(self.host,self.port)
            else:
                self.stop_server_thread()
    
    def set_master_mode(self):#NO VINCULADA
        self.master_button.setChecked(True)
        self.slave_button.setChecked(False)
            
        if self.mode == "master":
            
            return
        
        self.mode="master"
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
    
    def set_slave_mode(self):#NO VINCULADA
        self.master_button.setChecked(False)
        self.slave_button.setChecked(True)
        
        if self.mode == "slave":
            return
        
        self.mode="slave"
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
    
    def update_devices_lists(self):#TEST
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
    
    # TC Thread
    def start_tc_thread(self):#TEST
        self.tc_thread.init()
        self.tc_thread.start()

    def stop_tc_thread(self):#TEST
        self.tc_thread.stop()
    
    def get_tc_data(self,tc):#TEST
        self.tc_label.setText(tc)
        self.server_thread.update_tc_data(tc)
    
    def get_ltc_data(self,tc):#TEST
        if self.ltc_switch_state:
            self.ltc_tc_label.setText(tc)

    def get_mtc_data(self,tc):#TEST
        if self.mtc_switch_state:
            self.mtc_tc_label.setText(tc)

    # Server Thread
    def start_server_thread(self,host,port):#TEST
        self.server_thread.set_ip(host,port)
        self.server_thread.start()
        pass
    
    def stop_server_thread(self):#TEST
        self.server_thread.stop()
    
    def get_server_data(self,server_status):#TEST
        
        if server_status:
            self.connect_button.setText("ONLINE")
            self.connect_button.setStyleSheet(connected_button_stylesheet2)
            self.network_status = True
            self.users_icon_label.setVisible(True)
            self.users_label.setVisible(True)
        else:
            self.connect_button.setText("OFFLINE")
            self.connect_button.setStyleSheet(connected_button_stylesheet)
            self.network_status = False
            self.users_icon_label.setVisible(False)
            self.users_label.setVisible(False)
            
    def get_server_error(self, server_error):#TEST
        self.error_label.setText(server_error)
        
    def get_server_clients(self,clients):        
        self.clients = [elemento.getpeername()[0] for elemento in clients]       
        self.users_label.setText(str(len(self.clients)))
        
    # ----------------------BUTTONS FUNCTIONS-------------------------- 

    def play_pause(self):#TEST
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.start_tc_thread()
        else:
            self.stop_tc_thread()

    def stop(self):#TEST
        self.is_playing = False
        self.play_button.setChecked(False)
        self.stop_tc_thread()
        self.tc="00:00:00:00"
        self.tc_label.setText(self.tc)
        self.ltc_tc_label.setText(add_tcs(self.tc,self.ltc_offset,24))
        self.mtc_tc_label.setText(add_tcs(self.tc,self.mtc_offset,24))

    def forward(self):#TEST
        limit = Timecode(24, '23:49:59:00')
        tc = Timecode(24, self.tc)
        
        if self.tc > limit:
            tc = Timecode(24, f'23:59:59:{24-1}')
        else:
            for i in range(10 * 24):
                tc.next() 
                
        self.tc = str(tc)
        self.tc_label.setText(str(tc))       
        self.tc_thread.update_tc(tc)
        self.ltc_tc_label.setText(add_tcs(self.tc,self.ltc_offset,24))
        self.mtc_tc_label.setText(add_tcs(self.tc,self.mtc_offset,24))

    def backward(self):#TEST
        limit = Timecode(24, '00:00:10:00')
        tc = Timecode(24, self.tc)
        
        if self.tc < limit:
            tc = Timecode(24, '00:00:00:00')
        else:
            for i in range(10 * 24):
                tc.back()
        
        self.tc = str(tc)
        self.tc_label.setText(str(tc))       
        self.tc_thread.update_tc(tc)
        self.ltc_tc_label.setText(add_tcs(self.tc,self.ltc_offset,24))
        self.mtc_tc_label.setText(add_tcs(self.tc,self.mtc_offset,24))
            
    def tc_clock(self):#TEST
        current_time = datetime.datetime.now()
        current_time_str = current_time.strftime("%H:%M:%S:%f")[:-3] 
        tc = Timecode(24, start_timecode = current_time_str)
       
        self.tc = str(tc)
        self.tc_label.setText(str(tc))       
        self.tc_thread.update_tc(tc)
        self.ltc_tc_label.setText(add_tcs(self.tc,self.ltc_offset,24))
        self.mtc_tc_label.setText(add_tcs(self.tc,self.mtc_offset,24))

    def always_on_top(self):#TEST
        self.is_pin= not self.is_pin
        if self.windowFlags() & Qt.WindowStaysOnTopHint:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.show()

    def lock(self):#TEST
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
                self.master_button.setEnabled(True)
                self.slave_button.setEnabled(True)

    # ----------------------AUDIO FUNCTIONS--------------------------

    def opne_audio(self):#EMPTY
        pass  

    def close_audio(self):#EMPTY
        pass   

    def set_gain(self):#EMPTY
        pass
    
    def set_audio_device(self):#EMPTY
        pass

    # ----------------------LTC FUNCTIONS--------------------------
    
    def set_ltc_state(self):#TEST
        self.ltc_switch_state = not self.ltc_switch_state
        self.tc_thread.update_ltc_state()
        if self.ltc_switch_state:
            self.ltc_tc_label.setStyleSheet(f"color: #36BD74;")
            self.ltc_output_combo_box.setEnabled(False)
            self.ltc_fps_combo_box.setEnabled(False)
        else:
            self.ltc_tc_label.setText(self.ltc_offset)
            self.ltc_tc_label.setStyleSheet(f"color: #9a0d0d;")
            self.ltc_output_combo_box.setEnabled(True)
            self.ltc_fps_combo_box.setEnabled(True)
    
    def set_ltc_offset(self):#TEST
        
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
        
        self.ltc_offset = new_time
        self.ltc_offset_label.setText(new_time)
        
        if not self.ltc_switch_state or not self.is_playing:
            self.ltc_tc_label.setText(new_time)
            
        self.tc_thread.update_ltc_offset(self.ltc_offset)
        errase_values()
    
    def set_ltc_output(self):#TEST
        device_name = self.ltc_output_combo_box.currentText()
        index = None

        for clave, valor in self.audio_devices.items():
            if valor == device_name:
                index = clave
                break
            
        if index is not None and isinstance(index, int):
            self.tc_thread.update_audio_device(index)
    
    def set_ltc_fps(self):#TEST
        value = self.ltc_fps_combo_box.currentText()
        if value == "24 FPS":
            self.ltc_fps = 24
        elif value == "25 FPS":
            self.ltc_fps = 25
        elif value == "30 FPS":
            self.ltc_fps = 30
        self.tc_thread.update_ltc_fps(self.ltc_fps)
    
    # ----------------------MTC FUNCTIONS--------------------------

    def set_mtc_state(self):#TEST
        self.mtc_switch_state = not self.mtc_switch_state
        self.tc_thread.update_mtc_state()
        if self.mtc_switch_state:
            self.mtc_tc_label.setStyleSheet(f"color: #36BD74;")
            self.mtc_output_combo_box.setEnabled(False)
            self.mtc_fps_combo_box.setEnabled(False)
        else:
            self.mtc_tc_label.setText(self.ltc_offset)
            self.mtc_tc_label.setStyleSheet(f"color: #9a0d0d;")
            self.mtc_output_combo_box.setEnabled(True)
            self.mtc_fps_combo_box.setEnabled(True)
    
    def set_mtc_offset(self):#TEST
        
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
        
        self.mtc_offset = new_time
        self.mtc_offset_label.setText(new_time)
        
        if not self.mtc_switch_state or not self.is_playing:
            self.mtc_tc_label.setText(new_time)
        
        self.tc_thread.update_mtc_offset(self.mtc_offset)
        errase_values()
        
    def set_mtc_output(self):#TEST
        device_name = self.mtc_output_combo_box.currentText()
        index = None

        for clave, valor in self.midi_devices.items():
            if valor == device_name:
                index = clave
                break
            
        if index is not None and isinstance(index, int):
            self.tc_thread.update_midi_device(index)
    
    def set_mtc_fps(self):#TEST
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
    
    def __init__(self, parent = None):
        super(TC_Thread,self).__init__(parent)
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
        self.fps = 24
        frame_duration = 1 / self.fps
        
        self.tc = Timecode(24, self.tc)
        self.ltc_tc = Timecode(self.ltc_fps, self.ltc_tc)
        self.mtc_tc = Timecode(self.mtc_fps, self.mtc_tc)
        
        next_frame_time = time.time() + frame_duration
        
        while True:
            self.tc.next() #aumenta 1 frame
            if self.ltc_switch:
                self.ltc_tc = add_tcs(self.ltc_offset, self.tc, self.ltc_fps)
                audiodata = LTC.make_ltc_audio(self.ltc_tc)
                if self.audio_device.stream:
                    self.audio_device.play(audiodata)
            if self.mtc_switch:
                self.mtc_tc = add_tcs(self.mtc_offset,self.tc,self.mtc_fps)
                if self.midi_device.midi_out:
                    self.midi_device.sendMTC(self.mtc_tc)
                    
            #envia informacion
            self.tc_data.emit(str(self.tc)) 
            self.ltc_data.emit(str(self.ltc_tc))
            self.mtc_data.emit(str(self.mtc_tc))
            
            current_time = time.time()
            
            if current_time < next_frame_time:
                time.sleep(next_frame_time - current_time)
            
            next_frame_time += frame_duration
                
    def update_tc(self,tc):
        self.tc=tc
        
    def update_ltc_state(self):
        self.ltc_switch = not self.ltc_switch
    
    def update_mtc_state(self):
        self.mtc_switch = not self.mtc_switch
    
    def update_ltc_offset(self,offset):
        self.ltc_offset = offset
        
    def update_mtc_offset(self,offset):
        self.mtc_offset = offset
        
    def update_ltc_fps(self,fps):
        self.ltc_fps = fps
        
    def update_mtc_fps(self,fps):
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

class Server_Thread(QtCore.QThread):
    server_data = QtCore.pyqtSignal(bool)
    server_error = QtCore.pyqtSignal(str)
    server_clients = QtCore.pyqtSignal(list)
    
    def __init__(self, parent = None):
        super(Server_Thread,self).__init__(parent)
        self.is_running = True
        self.parent = parent
        self.online = False
        self.server_data.emit(self.online)
        self.server = None
        self.clientes_conectados = []
        self.data=""
        self.server_senders = []
        
    def set_ip(self,host="127.0.0.1",port=12345):
        self.host = host
        self.port = port
        self.direccion = f"{self.host}:{self.port}"
        
    def run(self):
        while True:
            try:
                self.server = socket(AF_INET, SOCK_STREAM)
                self.server.bind((self.host, self.port))
                log(f"[SERVER START ON]: {self.direccion}", GREEN)
                self.server.listen(5)
                log(f"[SERVER BROADCASTING ON]: {self.direccion}", GREEN)
                self.online = True
                self.server_data.emit(self.online)
                self.server_error.emit(f"")
                self.server.settimeout(1)
                lastdata = None
                
                while self.online:                   
                    readable, _, _ = select.select([self.server], [], [], 1)
                    if self.server in readable:
                        
                        client, address = self.server.accept()
                        log(f"[CLIENTE CONECTADO]: {address}", GREEN)
                        self.clientes_conectados.append(client)
                        self.server_clients.emit(self.clientes_conectados)
                            
                        self.server_sender = Server_sender(self,client, address)
                        self.server_sender.finished.connect(self.on_client_disconect)
                        self.server_sender.start()
                        
                        self.server_senders.append(self.server_sender)
                        
            except Exception as e:
                self.online = False
                self.server_data.emit(self.online)
                if "10048" in str(e):
                    self.server_error.emit("LAN UNAVAILABLE")
                if "10038" in str(e):
                    self.server_error.emit("SERVER STOPED")              
                if "10049" in str(e):
                    self.server_error.emit(f"INVALID IP")
                log(f"[SERVER DISCONECTED]: {e}", RED)
                break

    def on_client_disconect(self,client):
        for server_sender in self.server_senders:
            if str(server_sender.client) == str(client):
                self.server_senders.remove(server_sender)
                break 
            
        for elemento in self.clientes_conectados:
            if str(elemento) == str(client):
                self.clientes_conectados.remove(elemento)
                break
        self.server_clients.emit(self.clientes_conectados)      

    def update_tc_data(self,data):
        if self.server_senders != []:
            for server_sender in self.server_senders:
                server_sender.update_data(data)
        self.data = data
          
    def cerrar_server(self):
        self.online = False
        self.server_data.emit(self.online)
        if self.server:
            self.server.close()
            self.server = None
        log(f"[SERVER DICONECTED]: Stop Event cerrar_server", RED)
    
    def stop(self):
        self.cerrar_server()
        time.sleep(0.5)
        self.terminate()

class Server_sender(QtCore.QThread):
    finished = QtCore.pyqtSignal(str)
    
    def __init__(self,parent=None, client=None, address=None):
        super(Server_sender,self).__init__()
        self.parent = parent
        self.data = None
        self.client = client
        self.adress = address

    def run(self):
        last_data = None
        while True:
            try:
                if self.data != last_data:
                    data_str = str(self.data)
                    self.client.send(bytes(data_str, "utf-8"))
                last_data = self.data
                #self.client.recv(1024).decode()  #### ---------------- necesario para saber si se desconecta el client epero frena el codigo
            except Exception as e:
                log(f"[CLIENTE {self.adress} DESCONECTADO]: {e}", RED)
                break
        self.finished.emit(str(self.client))

    def update_data(self, data):
        self.data = data
        

# --------------------------EXEC----------------------------  

def main():
    mainApp = QApplication(sys.argv)
    app = UI()
    mainApp.exec_()    

if __name__ == "__main__":
    main()