from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QFrame
from PyQt5.QtGui import QMovie, QPainter, QColor, QBrush
from PyQt5.QtCore import Qt
import sys
from os import path

actual_path = path.abspath(path.dirname(__file__))
icon_url = path.join(actual_path, "img/load.gif").replace("\\", "/")

class LoadWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.resize(480, 320)

        self.initUI()

    def initUI(self):
        self.frame = QFrame(self)
        self.frame.setGeometry(90, 10, 300, 300)
        self.frame.setStyleSheet("background-color: transparent")

        self.label = QLabel(self.frame)
        self.movie = QMovie(icon_url)
        self.label.setMovie(self.movie)
        self.movie.start()

        # Ajustar el tamaño del QLabel al tamaño del marco
        self.label.setGeometry(self.frame.rect())

        # Escalar el tamaño del GIF al tamaño del marco
        self.movie.setScaledSize(self.frame.size())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        brush = QBrush(QColor(30, 30, 30, 255))
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)

        painter.drawRoundedRect(self.rect(), 20, 20)

def loading_window():
    app = QApplication(sys.argv)
    mainWindow = LoadWindow()
    mainWindow.show()
    sys.exit(app.exec_())

