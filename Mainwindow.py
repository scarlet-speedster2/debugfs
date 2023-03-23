import subprocess
from PyQt6.QtWidgets import QApplication, QMainWindow, QMenuBar, QMenu, QTextEdit


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Create a text editor widget
        self.textEdit = QTextEdit(self)
        self.setCentralWidget(self.textEdit)

        # Create a menu bar
        menuBar = QMenuBar(self)
        self.setMenuBar(menuBar)

        # Create a "File" menu
        fileMenu = QMenu('File', self)
        menuBar.addMenu(fileMenu)

        # Create a "Run Stats" action in the "File" menu
        runStatsAction = fileMenu.addAction('Stats')
        runStatsAction.triggered.connect(self.runStats)

        # Set the window title and show the window
        self.setWindowTitle('MainWindow')
        self.show()

    def runStats(self):
        # Run debugfs with the stats command and capture the output
        with subprocess.Popen(['sudo', 'debugfs', '/dev/sda3'], stdin=subprocess.PIPE, stdout=subprocess.PIPE) as proc:
            stats_output, _ = proc.communicate(b'stats\n')

        # Update the text editor with the output
        self.textEdit.setText(stats_output.decode())


if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    app.exec()
