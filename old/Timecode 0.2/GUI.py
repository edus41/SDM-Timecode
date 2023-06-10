import sys
import time
import multiprocessing as mlti

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


class WorkerGUI(QRunnable):
    def __init__(self, InFunc):
        super(WorkerGUI, self).__init__()
        self.Func = InFunc

    @pyqtSlot()
    def run(self):
        self.Func()


class ChildWindow(QWidget):
    def __init__(self, name):
        QWidget.__init__(self)
        self.Name = name
        print("Name :", name)
        self.setWindowTitle(self.Name)
        if name == "One":
            self.setGeometry(100, 100, 250, 100)
        else:
            self.setGeometry(100, 500, 250, 100)
        self.CountThis = False
        self.StartThis = True
        self.RunThis = True

        self.btnCnt = QPushButton("Cnt")
        self.btnCnt.clicked.connect(self.CountMe)

        self.lblCntr = QLabel()
        self.lblCntr.setText("0")

        HBox = QHBoxLayout()
        HBox.addWidget(self.btnCnt)
        HBox.addWidget(QLabel("     "))
        HBox.addWidget(self.lblCntr)
        HBox.addStretch(1)

        VBox = QVBoxLayout()
        VBox.addLayout(HBox)
        VBox.addStretch(1)

        self.setLayout(VBox)
        self.WrkrGUI = WorkerGUI(self.CountOnMe)

    def CountMe(self):
        if self.CountThis:
            self.btnCnt.setText("Cnt")
            self.CountThis = False
        else:
            self.btnCnt.setText("Off")
            self.CountThis = True
            if self.StartThis:
                self.StartThis = False
                self.threadpool = QThreadPool()
                self.threadpool.start(self.WrkrGUI)

    def CountOnMe(self):
        cnt = 0
        while self.RunThis:
            while self.CountThis:
                cnt += 1
                self.lblCntr.setText(str(cnt))
                time.sleep(0.01)
            time.sleep(0.01)


def Process2():
    MainThred = QApplication([])

    ChildGUI = ChildWindow("Two")
    ChildGUI.show()

    sys.exit(MainThred.exec_())


def Process1():
    MainThred = QApplication([])

    ChildGUI = ChildWindow("One")
    ChildGUI.show()

    sys.exit(MainThred.exec_())


if __name__ == "__main__":
    multiprcess1 = mlti.Process(target=Process1)
    multiprcess2 = mlti.Process(target=Process2)

    multiprcess1.start()
    multiprcess2.start()
