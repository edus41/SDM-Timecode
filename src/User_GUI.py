from PyQt5.QtWidgets import QWidget, QLabel, QFrame, QListWidget, QListWidgetItem, QStyledItemDelegate, QApplication
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QIcon
import os

actual_path = os.path.abspath(os.path.dirname(__file__))
icon_url = os.path.join(actual_path, "img/AppIcon2.png").replace("\\", "/")

class UsersWindow(QWidget):
    itemClicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("CLIENTS")
        self.setWindowIcon(QIcon(icon_url))
        self.setParent(parent)
        
        parent_position = parent.pos()
        screen_geometry = QApplication.desktop().screenGeometry()
        screen_width = screen_geometry.width()
        
        if parent_position.x() + 1190 < screen_width:
            x = parent_position.x() + 1010
        else:
            x = parent_position.x() - 190
            
        y = parent_position.y() + 300
            
        self.setGeometry(x, y, 180, 300)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.frame = QFrame(self)
        self.frame.setObjectName("Frame")
        self.frame.setGeometry(0, 0, 180, 300)
        self.frame.setStyleSheet("""
            QFrame#Frame {
                background: #202020;
                border-radius: 7px;
                border: 1px solid #36BD74;
            }
        """)

        self.title_label = QLabel("CLIENTS", self.frame)
        self.title_label.setGeometry(10, 10, 160, 30)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #36BD74;
                background-color: #222222;
                border-radius: 5px;
                font-family: IBM Plex Sans;
                font-size: 12px;
                font-weight: 75;
                font-weight: bold;
            }
        """)
        self.title_label.setAlignment(Qt.AlignCenter)
        
        self.ip_list = QListWidget(self.frame)
        self.ip_list.setGeometry(10, 40, 120, 230)
        self.ip_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border-top: 1px solid #505050;
                color: #AAAAAA;
                padding:0px;
                margin:0px;
                padding-top: 5px;
                font-family: "IBM Plex Sans";
                font-size: 12px;
                font-weight: bold;
            }
        """)
        self.ip_list.setSelectionMode(QListWidget.NoSelection)

        self.del_list = QListWidget(self.frame)
        self.del_list.setGeometry(130, 40, 40, 230)
        self.del_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border-top: 1px solid #505050;
                color: #B60F0F;
                text-align: center;
                padding:0px;
                margin:0px;
                padding-top: 5px;
                font-family: "IBM Plex Sans";
                font-size: 12px;
                font-weight: bold;
            }
        """)
        self.del_list.setItemDelegate(CenterAlignedDelegate())
        
        self.del_list.itemClicked.connect(self.del_client)
        self.frame.mouseMoveEvent = self.mouseMoveWindow

    def update_lists(self, clients):
        self.ip_list.clear()
        self.del_list.clear()

        for client in clients:
            ip_item = QListWidgetItem(client)
            del_item = QListWidgetItem("X")
            
            self.ip_list.addItem(ip_item)
            self.del_list.addItem(del_item)

    def del_client(self, item):
        item_index = self.del_list.row(item)
        self.itemClicked.emit(item_index) 

    def mousePressEvent(self, event):
        self.oldPosition = event.globalPos()

    def mouseMoveWindow(self, event):
        if hasattr(self, 'oldPosition'):
            delta = QPoint(event.globalPos() - self.oldPosition)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPosition = event.globalPos()

class CenterAlignedDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        option.displayAlignment = Qt.AlignCenter
        super().paint(painter, option, index)