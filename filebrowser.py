from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMenu,QTextEdit 
from stats import display_ext2_info
from PyQt5.QtWidgets import QDialog
import Mainwindow

class DebugfsBrowser(Mainwindow.Ui_MainWindow,QtWidgets.QMainWindow):

    def __init__(self):
        super(DebugfsBrowser,self).__init__()
        self.setupUi(self)
        self.stats()

    def stats(self):
        fileMenu = QMenu('File', self)
        self.menuBar().addMenu(fileMenu)
        runStatsAction = fileMenu.addAction('Stats')
        runStatsAction.triggered.connect(self.runStats)



    def runStats(self):
        # Run debugfs with the stats command and capture the output

        #print(stats_output)
        statwindow = StatWindow(self)
        statwindow.show()




class StatWindow(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowTitle('stats')
        self.setGeometry(10, 0, 741, 551)

        # Create a QTextEdit widget
        self.text_edit = QTextEdit(self)
        self.text_edit.setGeometry(10, 0, 741, 551)

        #print(type(self.stats))
        stats = display_ext2_info()
        self.text_edit.setText(stats)




if __name__ == '__main__':
    app = QApplication([])
    db_browser = DebugfsBrowser()
    db_browser.show()
    #main()
    app.exec()


