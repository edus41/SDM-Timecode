import os
import soundfile as sf
from pydub import AudioSegment
from PyQt5.QtWidgets import QFileDialog

def open_audio_file(self):
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