from multiprocessing import Process
import pyaudio
from tools import *
import time
from LTC_Generator import make_ltc_audio
from threading import Thread

##############################################
##--------------- LTC SENDER ---------------##
##############################################

class LTC_Sender(Process):
    
    def __init__(self, ltc_pipe):
        Process.__init__(self)
        self.pipe = ltc_pipe
        self.stream = None
        
        # RECV
        self.is_playing = False
        self.ltc_is_on = False
        self.ltc_output_device = 0
        self.ltc_fps = 25
        self.ltc_offset = 0
        self.timecode = 0
        self.ltc_timecode = 0
        
    def run (self):
        
        self.recive_thread = Thread(target = self.recive_data)
        self.recive_thread.start()
        
        self.p = pyaudio.PyAudio() 
        self.outputs = self.get_output_devices()
        self.ltc_output_device = next(iter(self.outputs))
        
        while True:
            last_frames_totales = -1
            while self.ltc_is_on and self.is_playing:
                frames_totales = int(self.timecode * self.ltc_fps)
                if last_frames_totales != frames_totales:
                    self.ltc_timecode = self.timecode + self.ltc_offset
                    self.ltc_tc = secs_to_tc(self.ltc_timecode, self.ltc_fps)
                    audio_data = make_ltc_audio(self.ltc_tc)
                    self.play(audio_data)
                last_frames_totales = frames_totales
                time.sleep(0.01)
            time.sleep(0.1)
        
    def play(self, audio_data):
        if not self.stream:
            self.abrir_stream()
        self.stream.write(audio_data)
    
    def set_output_device(self, device_index):

        num_devices = self.p.get_host_api_info_by_index(0).get('deviceCount')        
        if device_index >= num_devices:
            print(f"El índice del dispositivo ({device_index}) es inválido.")
            return

        dispositivo_info = self.p.get_device_info_by_index(device_index)
        if dispositivo_info['maxOutputChannels'] == 0:
            print("El dispositivo seleccionado no es un dispositivo de salida válido.")
            return
            
        self.ltc_output_device = device_index
        print(f"Dispositivo de salida configurado: {dispositivo_info['name']}")
    
        if self.stream:
            self.cerrar_stream()
            self.abrir_stream()
    
    def get_output_devices(self):
        output_devices = {}
        num_devices = self.p.get_host_api_info_by_index(0).get('deviceCount') 
        for i in range(0, num_devices):
            name = self.p.get_device_info_by_host_api_device_index(0, i).get('name')
            device_id = self.p.get_device_info_by_host_api_device_index(0, i).get('index')
            
            if self.p.get_device_info_by_host_api_device_index(0, i).get('maxOutputChannels') > 0 and name != "Asignador de sonido Microsoft - Output":
                output_devices[device_id] = name
        return output_devices
    
    
    def configurar_formato(self, rate=44100, bits=16, channels=2):

        self.format = self.p.get_format_from_width(bits // 8)
        self.rate = rate
        self.channels = channels
        
        if self.stream:
            self.cerrar_stream()
            self.abrir_stream()
     
    def abrir_stream(self):
        self.stream = self.p.open(output_device_index=self.ltc_output_device,
                format = self.p.get_format_from_width(16 // 8),
                channels = 1,
                rate = 44100,
                output = True)

    def cerrar_stream(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.stream = None
            
    def close(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        self.p.terminate()
        self.p = None
    
    # COMINICATION
    def recive_data(self):
        while True:
            recive_data = self.pipe.recv()
            if 'is_playing' in recive_data:
                self.is_playing = recive_data["is_playing"]
                
            if 'ltc_is_on' in recive_data:
                self.ltc_is_on = recive_data["ltc_is_on"]
                
            if 'ltc_output_device' in recive_data:
                self.ltc_output_device = recive_data["ltc_output_device"]
                self.set_output_device(self.ltc_output_device)

            if 'ltc_fps' in recive_data:
                self.ltc_fps = recive_data["ltc_fps"] 
                   
            if 'ltc_offset' in recive_data:
                self.ltc_offset = recive_data["ltc_offset"]
                
            if 'tc' in recive_data:
                self.timecode = recive_data["tc"]

