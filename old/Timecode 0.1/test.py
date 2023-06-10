import sys
import datetime
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton

class TimecodeApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Timecode App")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        self.time_labels = []

        # Crear cuatro etiquetas para los códigos de tiempo
        for _ in range(4):
            time_label = QLabel(self)
            layout.addWidget(time_label)
            self.time_labels.append(time_label)

        self.play_pause_button = QPushButton("Play", self)
        layout.addWidget(self.play_pause_button)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)

        self.is_playing = False
        self.start_time = None
        self.fps_values = [99, 24, 25, 30]  # Tasa de fotogramas por segundo para cada código de tiempo

    def toggle_play_pause(self):
        if self.is_playing:
            self.timer.stop()
            self.play_pause_button.setText("Play")
        else:
            if not self.start_time:
                self.start_time = datetime.datetime.now()
            self.timer.start(33)  # Actualiza el tiempo aproximadamente cada 33 milisegundos (para 30 FPS)
            self.play_pause_button.setText("Pause")
        self.is_playing = not self.is_playing

    def update_time(self):
        if self.start_time:
            elapsed_time = datetime.datetime.now() - self.start_time
            total_seconds = elapsed_time.total_seconds()

            # Actualizar el código de tiempo para cada tasa de fotogramas
            for i, fps in enumerate(self.fps_values):
                frames = int(total_seconds * fps) % fps
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                timecode = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}:{frames:02d}"
                self.time_labels[i].setText(timecode)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TimecodeApp()
    window.setGeometry(100, 100, 240, 250)
    window.show()
    sys.exit(app.exec_())
