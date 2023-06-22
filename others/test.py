import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton

class Ventana(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Ventana con Labels')
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()
        self.setLayout(layout)

        btn = QPushButton('Abrir Ventana', self)
        btn.clicked.connect(self.abrirVentana)
        layout.addWidget(btn)

    def abrirVentana(self):
        ventana_labels = QWidget()
        ventana_labels.setWindowTitle('Ventana de Labels')
        ventana_labels.setGeometry(200, 200, 300, 200)

        layout_labels = QVBoxLayout()
        ventana_labels.setLayout(layout_labels)

        label1 = QLabel('Label 1')
        layout_labels.addWidget(label1)

        label2 = QLabel('Label 2')
        layout_labels.addWidget(label2)

        label3 = QLabel('Label 3')
        layout_labels.addWidget(label3)

        ventana_labels.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ventana_principal = Ventana()
    ventana_principal.show()
    sys.exit(app.exec_())
