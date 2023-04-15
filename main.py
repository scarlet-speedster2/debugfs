import sys
import os
import platform
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import (QCoreApplication, QPropertyAnimation, QDate, QDateTime, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt, QEvent)
from PySide2.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QIcon, QKeySequence, QLinearGradient, QPalette, QPainter, QPixmap, QRadialGradient)
from PySide2.QtWidgets import *

# Import user interface file
from MainWindow import *

# Global value for the windows status
WINDOW_SIZE = 0;

# Main class
class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowTitle("Debugfs Browser")

        # Remove window tlttle bar
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint) 

        # Set main background to transparent
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
      
        # Apply shadow effect
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QColor(0, 92, 157, 150))
        # Appy shadow to central widget
        self.ui.centralwidget.setGraphicsEffect(self.shadow)

        # Button click events to our top bar buttons
        # 
        #Minimize window
        self.ui.minimizeButton.clicked.connect(lambda: self.showMinimized())
        #Close window
        self.ui.closeButton.clicked.connect(lambda: self.close())
        #Restore/Maximize window
        self.ui.restoreButton.clicked.connect(lambda: self.restore_or_maximize_window())
        def moveWindow(e):
            if self.isMaximized() == False: #Not maximized
                if e.buttons() == Qt.LeftButton:
                    #Move window 
                    self.move(self.pos() + e.globalPos() - self.clickPosition)
                    self.clickPosition = e.globalPos()
                    e.accept()
        self.ui.main_header.mouseMoveEvent = moveWindow

        # SLIDABLE LEFT MENU/////////////////
        #Left Menu toggle button
        self.ui.left_menu_toggle_btn.clicked.connect(lambda: self.slideLeftMenu())
        #Set the page that will be visible by default when the app is opened
        self.ui.stackedWidget.setCurrentWidget(self.ui.home_page)
        # ###############################################
        # //////////////////////////////////////

        # STACKED PAGES NAVIGATION/////////////////
        #Using side menu buttons

        #navigate to Home page
        self.ui.home_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.home_page))



        for w in self.ui.left_side_menu.findChildren(QPushButton):
            # Add click event listener
            w.clicked.connect(self.applyButtonStyle)
        #################################################################################
        QSizeGrip(self.ui.size_grip)
        #################################################################################
        # Window Size grip
        # Show window
        self.show()
        # ###############################################

    def applyButtonStyle(self):
        # Reset style for other buttons
        for w in self.ui.left_side_menu.findChildren(QPushButton):
            # If the button name is not equal to clicked button name
            if w.objectName() != self.sender().objectName():
                # Create default style by removing the left border
                # Lets remove the bottom border style
                defaultStyle = w.styleSheet().replace("border-bottom: 2px solid  rgb(0, 136, 255);", "")

                # Lets also remove the left border style
                defaultStyle = defaultStyle.replace("border-left: 2px solid  rgb(0, 136, 255);", "")

                # Apply the default style
                w.setStyleSheet(defaultStyle)
                #                 
        newStyle = self.sender().styleSheet() + ("border-left: 2px solid  rgb(0, 136, 255);border-bottom: 2px solid  rgb(0, 136, 255);")
        # Apply the new style
        self.sender().setStyleSheet(newStyle)
        # 
        return


    # Add mouse events to the window
    def mousePressEvent(self, event):
        self.clickPosition = event.globalPos()

    # Restore or maximize your window
    def restore_or_maximize_window(self):
        # Global windows state
        global WINDOW_SIZE #The default value is zero to show that the size is not maximized
        win_status = WINDOW_SIZE

        if win_status == 0:
        	# If the window is not maximized
        	WINDOW_SIZE = 1 #Update value to show that the window has been maxmized
        	self.showMaximized()

        	# Update button icon  when window is maximized
        	self.ui.restoreButton.setIcon(QtGui.QIcon(u"./icons/cil-window-restore.png"))#Show minized icon
        else:
        	# If the window is on its default size
            WINDOW_SIZE = 0 #Update value to show that the window has been minimized/set to normal size (which is 800 by 400)
            self.showNormal()

            # Update button icon when window is minimized
            self.ui.restoreButton.setIcon(QtGui.QIcon(u"./icons/cil-window-maximize.png"))#Show maximize icon
    def slideLeftMenu(self):
        # Get current left menu width
        width = self.ui.left_side_menu.width()

        # If minimized
        if width == 50:
            # Expand menu
            newWidth = 150
        # If maximized
        else:
            # Restore menu
            newWidth = 50

        # Animate the transition
        self.animation = QPropertyAnimation(self.ui.left_side_menu, b"minimumWidth")#Animate minimumWidht
        self.animation.setDuration(250)
        self.animation.setStartValue(width)#Start value is the current menu width
        self.animation.setEndValue(newWidth)#end value is the new menu width
        self.animation.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
        self.animation.start()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())


