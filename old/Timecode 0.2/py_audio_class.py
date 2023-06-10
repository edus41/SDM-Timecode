import pyaudio


class AudioDevice:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.num_devices = self.p.get_host_api_info_by_index(0).get('deviceCount')
        self.format = self.p.get_format_from_width(16 // 8)
        self.rate = 44100
        self.channels = 1
        self.output_devices=self.get_output_devices()
        self.current_output_device_index=next(iter(self.output_devices))
        self.gain=0
        
        self.abrir_stream()
        
    def get_output_devices(self):
        output_devices = {}
        
        for i in range(0, self.num_devices):
            name = self.p.get_device_info_by_host_api_device_index(0, i).get('name')
            device_id = self.p.get_device_info_by_host_api_device_index(0, i).get('index')
            
            if self.p.get_device_info_by_host_api_device_index(0, i).get('maxOutputChannels') > 0 and name != "Asignador de sonido Microsoft - Output":
                output_devices[device_id] = name
        return output_devices

    def set_output_device(self, new_device_index):
        if self.stream:
            self.cerrar_stream()
            
        if new_device_index >= self.num_devices:
            print(f"El índice del dispositivo ({new_device_index}) es inválido.")
            return

        dispositivo_info = self.p.get_device_info_by_index(new_device_index)
        if dispositivo_info['maxOutputChannels'] == 0:
            print("El dispositivo seleccionado no es un dispositivo de salida válido.")
            return
            
        self.current_output_device_index = new_device_index
        print(f"Dispositivo de salida configurado: {dispositivo_info['name']}")
    
        self.abrir_stream()
        
    def configurar_formato(self, rate=44100, bits=16, channels=2):

        self.format = self.p.get_format_from_width(bits // 8)
        self.rate = rate
        self.channels = channels
        
        if self.stream:
            self.cerrar_stream()
        
    def play(self, audio_data):
        if not self.stream:
            self.abrir_stream()
        self.stream.write(audio_data)
        
    def abrir_stream(self):
        self.stream = self.p.open(output_device_index=self.current_output_device_index,
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                output=True)

    def cerrar_stream(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.stream = None
    
    def clear(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate() 
          

