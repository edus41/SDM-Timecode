import pygame.midi
import time

class MidiDevice:
    def __init__(self):
        pygame.midi.init()
        self.device_count = pygame.midi.get_count()
        self.output_devices = self.get_all_output_devices()
        self.current_output_device_index = next(iter(self.output_devices))
        self.midi_out = pygame.midi.Output(self.current_output_device_index)
        
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
    
    def sendMidi(self,data):
        data1=data[0]
        data2=data[1]
        self.midi_out.write_short(data1,data2)    
    
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
    
    def clear(self):
        pygame.midi.quit()
        self.midi_out = None
        