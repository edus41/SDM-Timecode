from multiprocessing import Process
import multiprocessing
from threading import Thread
import time
from socket import *
import numpy as np
import sounddevice as sd
from tools import *
import os
import datetime
#from pydub import AudioSegment
import soundfile as sf
##############################################
##----------------- PLAYER -----------------##
##############################################

class Player(Process):
    
    def __init__(self, player_pipe):
        Process.__init__(self)
        self.pipe = player_pipe
        self.fps = 99
        self.stream = None
        self.time_start = 0
        self.audio_data = None
        self.sample_rate = None
        self.paused_sample = 0
        self.current_sample = 0
        
        #  SEND
        self.timecode = 0
        self.audio_total_duration = 0
        
        # PLAYER RECV
        self.is_running = True
        self.is_playing = False
        self.audio_device = None
        self.gain = 0.8
        self.file_path = None

    def run(self):
        try:
            self.recive_thread = Thread(target = self.recive_data)
            self.recive_thread.start()
            self.send_thread = Thread(target = self.send_data)
            self.send_thread.start()

            while self.is_running:
                if self.is_playing:
                    if self.sample_rate != None:
                        self.play_audio()
                    else:
                        self.play_tc()
                time.sleep(0.1)
        except Exception as e:
            print(f"[ERROR PLAYER]: {e}")

    def play_tc(self):
        try:
            while self.is_playing and self.timecode < 86399.9999 and self.is_running:
                self.timecode = round(time.time() - self.time_start ,2)
                time.sleep(1 / self.fps)
            time.sleep(0.1)
        except Exception as e:
            print(f"[ERROR PLAYER]: {e}")
        
    def play_audio(self):
        try:
            self.stream = sd.OutputStream(
                callback=self.audio_callback,
                channels=self.audio_data.shape[1],
                samplerate=self.sample_rate,
                device=self.audio_device,
            )

            with self.stream:
                while self.is_playing and self.current_sample < len(self.audio_data) and self.is_running:
                    time.sleep(0.01)
        except Exception as e:
            print(f"[ERROR PLAYER]: {e}")

    def audio_callback(self, outdata, ff, time, status):#OK
        try:
            if self.is_playing:
                if self.current_sample < len(self.audio_data):
                    outdata[:ff, :] = np.resize(
                        self.audio_data[self.current_sample : self.current_sample + ff, :],
                        (ff, 2),
                    ) * self.gain
                    self.current_sample += ff
                    segundo_actual = round((self.current_sample / self.sample_rate ) - (2 / self.fps),2)
                    self.timecode = segundo_actual
            else:
                outdata[:ff, :] = np.resize(
                        0,
                        (ff, 2),
                    ) * 0
        except Exception as e:
            print(f"[ERROR PLAYER]: {e}")

    def play_pause(self):
        self.time_start = time.time() - self.timecode   
        self.paused_sample = self.current_sample
        
    def clock(self):
        try:
            if self.audio_data is None:
                date_time = datetime.datetime.now()
                midnight_time = date_time.replace(hour = 0, minute = 0, second = 0, microsecond = 0)
                dif = date_time - midnight_time
                elapsed_time = dif.total_seconds()
                self.time_start = time.time() - elapsed_time 
                self.timecode = elapsed_time
        except Exception as e:
            print(f"[ERROR PLAYER]: {e}")
            
    def forward(self):
        if self.audio_data is None:
            if self.timecode + 10 < 86400:
                self.time_start = self.time_start - 10
                self.timecode = self.timecode + 10
            else:
                self.time_start = self.time_start + 86400
                self.timecode = 86400
        else:
            if self.current_sample + (self.sample_rate * 10) < len(self.audio_data):
                self.current_sample = self.current_sample + (self.sample_rate * 10)
                self.timecode = self.timecode + 10
            else:
                self.current_sample = len(self.audio_data)
                self.timecode = self.audio_total_duration

    def backward(self):
        if self.audio_data is None:
            if self.timecode - 10 > 0:
                self.time_start = self.time_start + 10
                self.timecode = self.timecode - 10
            else:
                self.time_start = time.time()
                self.timecode = 0
        else:
            if self.current_sample - (self.sample_rate * 10) > 0:
                self.current_sample = self.current_sample - (self.sample_rate * 10)
                self.timecode = self.timecode - 10
            else:
                self.current_sample = 0
                self.timecode = 0

    def open_audio(self):
        try:
            if self.file_path:
                _, file_extension = os.path.splitext(self.file_path)
                file_extension = file_extension.lower()

                if file_extension == '.wav':
                    audio_data, sample_rate = sf.read(self.file_path)
                #elif file_extension == '.mp3':
                #    audio = AudioSegment.from_mp3(self.file_path)
                #    temp_file_path = 'temp.wav'
                #    audio.export(temp_file_path, format='wav')
                #    audio_data, sample_rate = sf.read(temp_file_path)
                #    os.remove(temp_file_path)
                else:
                    raise ValueError('Formato de archivo no válido.')
                
                self.audio_total_duration = len(audio_data) / sample_rate
                self.pipe.send({"total_duration":self.audio_total_duration})
                self.audio_data = audio_data
                self.sample_rate = sample_rate
                
        except Exception as e:
            print('[OPEN AUDIO ERROR]:', str(e))

    def close_audio(self):
        try:
            self.audio_data = None
            self.sample_rate = None
            self.pipe.send({"total_duration":None})
        except Exception as e:
            print(f"[ERROR PLAYER]: {e}")

    # COMINICATION
    def recive_data(self):
        try:
            while self.is_running:
                recive_data = self.pipe.recv()

                if 'is_playing' in recive_data:
                    self.is_playing = recive_data["is_playing"]
                    self.play_pause() 
                    
                if 'stop' in recive_data:
                    self.timecode = 0
                    self.current_sample = 0

                if 'clock' in recive_data:
                    self.clock()

                if 'forward' in recive_data:
                    self.forward()

                if 'backward' in recive_data:
                    self.backward()

                if 'open_audio' in recive_data:
                    self.open_audio()

                if 'close_audio' in recive_data:
                    self.close_audio()

                if 'is_running' in recive_data:
                    self.close()  

                if 'file_path' in recive_data:
                    self.file_path = recive_data["file_path"]
                    if self.file_path is not None:
                        self.open_audio()
                    else:
                        self.close_audio()
                        
                if 'audio_device' in recive_data:
                    self.audio_device = recive_data["audio_device"]  

                if 'gain' in recive_data:
                    self.gain = recive_data["gain"] 
                    
        except Exception as e:
            print(f"[ERROR PLAYER]: {e}")
            
    def send_data(self):
        try:
            self.last_current_sample = self.current_sample
            self.last_tc = self.timecode
            self.audio_total_duration = self.audio_total_duration
            
            while self.is_running:
                data_to_send = {}
                if self.last_tc != self.timecode:
                    data_to_send['tc'] = self.timecode
                    self.last_tc = self.timecode
                
                if data_to_send:
                    self.pipe.send(data_to_send)
                    
        except Exception as e:
            print(f"[ERROR PLAYER]: {e}")
    # END
    def close(self):
        try:
            self.is_running = False
            self.is_playing = False
            self.recive_thread.join()
            proceso_actual = multiprocessing.current_process()
            proceso_actual.terminate()  
        except Exception as e:
            print(f"[ERROR PLAYER]: {e}")
