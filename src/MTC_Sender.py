from multiprocessing import Process
import pygame.midi
from tools import *
import time
from threading import Thread
##############################################
##--------------- MTC SENDER ---------------##
##############################################

class MTC_Sender(Process):
    
    def __init__(self,mtc_pipe):
        Process.__init__(self)
        self.pipe = mtc_pipe
        self.midi_out = None
        
        # RECV
        self.is_playing = False
        self.mtc_is_on = False
        self.mtc_output_device = 0
        self.mtc_fps = 25
        self.mtc_offset = 0
        self.timecode = 0
        self.mtc_timecode = 0
        
    def run (self):
        self.recive_thread = Thread(target = self.recive_data)
        self.recive_thread.start()
        
        pygame.midi.init()
        self.device_count = pygame.midi.get_count()
        self.output_devices = self.get_all_output_devices()
        self.pipe.send({"mtc_devices":self.output_devices})
        self.current_output_device_index = next(iter(self.output_devices))
        self.midi_out = pygame.midi.Output(self.current_output_device_index)
        
        while True:
            last_frames_totales = -1
            while self.mtc_is_on and self.is_playing:
                frames_totales = int(self.timecode * self.mtc_fps)
                if last_frames_totales != frames_totales:
                    self.mtc_timecode = self.timecode + self.mtc_offset
                    self.mtc_tc = secs_to_tc(self.mtc_timecode, self.mtc_fps)
                    self.sendMTC(self.mtc_tc)
                last_frames_totales = frames_totales
                time.sleep(0.01)
            time.sleep(0.1)
        
    def get_all_output_devices(self):
        devices = {}
        for i in range(self.device_count):
            device_info = pygame.midi.get_device_info(i)
            if device_info[3] > 0 and device_info[1] != b'Microsoft MIDI Mapper' and device_info[1] != b'Microsoft GS Wavetable Synth':
                devices[i] = device_info[1].decode("utf-8")
                
        return devices
    
    def set_output_device(self,device_index):
        if self.midi_out:
            self.midi_out.close()
        pygame.midi.quit()
        pygame.midi.init()
        self.midi_out = pygame.midi.Output(device_index)
        self.current_output_device_index = device_index
        print(f"new: {device_index} : {pygame.midi.get_device_info(device_index)[1]}")
    
    def sendMTC(self,timecode):
        timecode_str = str(timecode)
        hh = int(timecode_str[:2])
        mm = int(timecode_str[3:5])
        ss = int(timecode_str[6:8])
        ff = int(timecode_str[9:])
        
        digit1 = ff - 16 if ff >= 16 else ff
        digit2 = 17 if ff >= 16 else 16
        digit3 = ss - (ss // 16) * 16 + 32 if ss >= 16 else ss + 32
        digit4 = ss // 16 + 48
        digit5 = mm - (mm // 16) * 16 + 64 if mm >= 16 else mm + 64
        digit6 = mm // 16 + 80
        digit7 = hh - (hh // 16) * 16 + 96 if hh >= 16 else hh + 96
        digit8 = hh // 16 + 114

        self.midi_out.write_short(0xF1, digit1)
        self.midi_out.write_short(0xF1, digit2)
        self.midi_out.write_short(0xF1, digit3)
        self.midi_out.write_short(0xF1, digit4)
        self.midi_out.write_short(0xF1, digit5)
        self.midi_out.write_short(0xF1, digit6)
        self.midi_out.write_short(0xF1, digit7)
        self.midi_out.write_short(0xF1, digit8)
    
    def close(self):
        pygame.midi.quit()
        self.midi_out = None

    # COMINICATION
    def recive_data(self):
        while True:
            recive_data = self.pipe.recv()
            
            if 'is_playing' in recive_data:
                self.is_playing = recive_data["is_playing"]
                
            if 'mtc_is_on' in recive_data:
                self.mtc_is_on = recive_data["mtc_is_on"]
                
            if 'mtc_output_device' in recive_data:
                self.mtc_output_device = recive_data["mtc_output_device"]
                self.set_output_device(self.mtc_output_device)

            if 'mtc_fps' in recive_data:
                self.mtc_fps = recive_data["mtc_fps"] 
                   
            if 'mtc_offset' in recive_data:
                self.mtc_offset = recive_data["mtc_offset"]
                
            if 'tc' in recive_data:
                self.timecode = recive_data["tc"]
