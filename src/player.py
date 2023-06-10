from multiprocessing import Process
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
import time
from socket import *
import numpy as np
import sounddevice as sd
from tools import *


##############################################
##----------------- PLAYER -----------------##
##############################################

class Player(Process):
    
    def __init__(self, player_pipe):
        Process.__init__(self)
        self.pipe = player_pipe
        self.fps = 99
        self.stream = None
        
        #  SEND
        self.timecode = 0
        
        # PLAYER RECV
        self.is_playing = False
        self.time_start = 0
        self.audio_data = None
        self.sample_rate = None
        self.paused_sample = 0
        self.audio_device = None
        self.gain = 0.8
        self.current_sample = 0
        
        # SEND COMPARISON
        self.last_current_sample = self.current_sample
        self.last_tc = self.timecode

    def run(self):
        self.recive_thread = Thread(target = self.recive_data)
        self.recive_thread.start()
        while True:
            if self.is_playing:
                if self.sample_rate != None:
                    self.play_audio()
                else:
                    self.play_tc()
            time.sleep(0.1)

    def play_tc(self):
        while self.is_playing and self.timecode < 86399.9999:
            self.timecode = time.time() - self.time_start 
            self.send_data()
            time.sleep(1 / self.fps)
        time.sleep(0.1)
        
    def play_audio(self):
        self.stream = sd.OutputStream(
            callback=self.audio_callback,
            channels=self.audio_data.shape[1],
            samplerate=self.sample_rate,
            device=self.audio_device,
        )

        with self.stream:
            while self.is_playing and self.current_sample < len(self.audio_data) :
                time.sleep(0.01)  # Pequeña pausa para evitar bloquear la CPU

    def audio_callback(self, outdata, ff, time, status):#OK
        if self.is_playing:
            if self.current_sample < len(self.audio_data):
                outdata[:ff, :] = np.resize(
                    self.audio_data[self.current_sample : self.current_sample + ff, :],
                    (ff, 2),
                ) * self.gain
                self.current_sample += ff
                segundo_actual = (self.current_sample / self.sample_rate ) - (2 / self.fps)
                self.timecode = segundo_actual
                self.send_data()
        else:
            outdata[:ff, :] = np.resize(
                    0,
                    (ff, 2),
                ) * 0

    # COMINICATION
    def recive_data(self):
        while True:
            recive_data = self.pipe.recv()
            
            if 'is_playing' in recive_data:
                self.is_playing = recive_data["is_playing"]
                if self.is_playing:
                    if self.paused_sample != 0:
                        self.current_sample = self.paused_sample
                    elif self.paused_sample == 0:
                        self.current_sample = 0
            if 'time_start' in recive_data:
                self.time_start = recive_data["time_start"]    
            if 'audio_data' in recive_data:
                self.audio_data = recive_data["audio_data"]
            if 'sample_rate' in recive_data:
                self.sample_rate = recive_data["sample_rate"]     
            if 'paused_sample' in recive_data:
                self.paused_sample = recive_data["paused_sample"]
                if self.paused_sample == 0:
                    self.current_sample = 0
            if 'audio_device' in recive_data:
                self.audio_device = recive_data["audio_device"]    
            if 'gain' in recive_data:
                self.gain = recive_data["gain"]   
           
    def send_data(self):
        data_to_send = {}
        
        if self.last_current_sample != self.current_sample:
            data_to_send['current_sample'] = self.current_sample
            self.last_current_sample = self.current_sample
            
        if self.last_tc != self.timecode:
            data_to_send['tc'] = self.timecode
            self.last_tc = self.timecode
        
        if data_to_send:
            self.pipe.send(data_to_send)
            