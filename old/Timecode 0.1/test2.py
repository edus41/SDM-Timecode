import sys
import datetime
import time
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton

import requests

class TimecodeApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Timecode App")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        self.time_label = QLabel(self)
        layout.addWidget(self.time_label)

        self.start_button = QPushButton("Start", self)
        layout.addWidget(self.start_button)
        self.start_button.clicked.connect(self.start_timecode)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)

        self.is_playing = False
        self.start_time = None
        self.fps = 30  # Tasa de fotogramas por segundo

    def start_timecode(self):
        duration = 10  # Duración en segundos
        frame_rate = 30  # Tasa de fotogramas por segundo

        response = requests.post('http://localhost:5000/api/start', json={
            'duration': duration,
            'frame_rate': frame_rate
        })
        # Procesar la respuesta si es necesario

        if not self.start_time:
            self.start_time = datetime.datetime.now()
        self.timer.start(33)  # Actualiza el tiempo aproximadamente cada 33 milisegundos (para 30 FPS)
        self.start_button.setEnabled(False)

    def update_time(self):
        if self.start_time:
            elapsed_time = datetime.datetime.now() - self.start_time
            total_seconds = elapsed_time.total_seconds()
            frames = int(total_seconds * self.fps) % self.fps
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            timecode = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}:{frames:02d}"
            self.time_label.setText(timecode)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TimecodeApp()
    window.setGeometry(100, 100, 240, 100)
    window.show()
    sys.exit(app.exec_())
