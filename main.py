from Mainwindow import MainWindow
from PyQt6.QtWidgets import QApplication
if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    app.exec()


#sudo -E env PATH=$PATH python3 main.py
