

import sys
import os
import platform
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import (QCoreApplication, QPropertyAnimation, QDate, QDateTime, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt, QEvent)
from PySide2.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QIcon, QKeySequence, QLinearGradient, QPalette, QPainter, QPixmap, QRadialGradient)
from PySide2.QtWidgets import *
from time import sleep, perf_counter
from threading import Thread
from collections import deque
from PySide2.QtCore import Signal,QObject
from ext2 import *
import ext

import constants
constants.FileName = sys.argv[1]
# Import user interface file
from MainWindow import *

# Global value for the windows status
WINDOW_SIZE = 0;
# This will help us determine if the window is minimized or maximized

# Main class
class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.it = None
        self.workingDir = None
        self.fs = None

        # Set window Icon
        # This icon and title will not appear on our app main window because we removed the title bar
        self.setWindowIcon(QtGui.QIcon(":/images/images/cil-4k.png"))
        # Set window tittle
        self.setWindowTitle("Debugfs browser")

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


        # 
        #Minimize window
        self.ui.minimizeButton.clicked.connect(lambda: self.showMinimized())
        #Close window
        self.ui.closeButton.clicked.connect(lambda: self.close())
        #Restore/Maximize window
        self.ui.restoreButton.clicked.connect(lambda: self.restore_or_maximize_window())
        # ###############################################
        def moveWindow(e):
            # Detect if the window is  normal size
            # ###############################################  
            if self.isMaximized() == False: #Not maximized
                # Move window only when window is normal size  
                # ###############################################
                #if left mouse button is clicked (Only accept left mouse button clicks)
                if e.buttons() == Qt.LeftButton:  
                    #Move window 
                    self.move(self.pos() + e.globalPos() - self.clickPosition)
                    self.clickPosition = e.globalPos()
                    e.accept()
        self.ui.main_header.mouseMoveEvent = moveWindow
        #Left Menu toggle button
        self.ui.left_menu_toggle_btn.clicked.connect(lambda: self.slideLeftMenu())
        self.ui.stackedWidget.setCurrentWidget(self.ui.home_page)
        self.ui.home_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.home_page))
        self.ui.accounts_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.accounts_page))
        
        self.ui.settings_button.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.settings_page))
        for w in self.ui.left_side_menu.findChildren(QPushButton):
            # Add click event listener
            w.clicked.connect(self.applyButtonStyle)

        QSizeGrip(self.ui.size_grip)

        # self.item1 =None
        # fs = None
        # try:
        #     self.fs = Ext2Filesystem.fromImageFile(constants.FileName)
        #     with self.fs:
        #         self.workingDir = self.fs.rootDir
        #         op, self.workingDir = ext.shell(self.fs, self.workingDir, 'ls -li')
        #         for i in op:
        #             self.item1 = QTreeWidgetItem(i)
        #             self.ui.treeWidget.addTopLevelItem(self.item1)
        #         self.ui.treeWidget.itemClicked.connect(self.on_item_clicked)
        #         op, self.workingDir = ext.shell(self.fs, self.workingDir, 'ls -li')

        #
        # except IOError:
        #     print("Could not read device file .")


        self.show()
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

        # Apply new style to clicked button
        # Sender = clicked button
        # Get the clicked button stylesheet then add new left-border style to it
        # Lets add the bottom border style
        newStyle = self.sender().styleSheet() + ("border-left: 2px solid  rgb(0, 136, 255);border-bottom: 2px solid  rgb(0, 136, 255);")
        # Apply the new style
        self.sender().setStyleSheet(newStyle)
        # 
        return



    def mousePressEvent(self, event):
        # ###############################################
        # Get the current position of the mouse
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
        	self.ui.restoreButton.setIcon(QtGui.QIcon(u":/icons/icons/cil-window-restore.png"))#Show minized icon
        else:
        	# If the window is on its default size
            WINDOW_SIZE = 0 #Update value to show that the window has been minimized/set to normal size (which is 800 by 400)
            self.showNormal()

            # Update button icon when window is minimized
            self.ui.restoreButton.setIcon(QtGui.QIcon(u":/icons/icons/cil-window-maximize.png"))#Show maximize icon

    def root_item(self):
        # Create a root item and add it to the tree
         try:

            self.fs = Ext2Filesystem.fromImageFile(constants.FileName)
            with self.fs:
                self.workingDir = self.fs.rootDir
                op, self.workingDir = ext.shell(self.fs, self.workingDir, 'ls -li')
                for i in op:
                    self.item1 = QTreeWidgetItem(i)
                    self.ui.treeWidget.addTopLevelItem(self.item1)
                self.ui.treeWidget.itemClicked.connect(self.add_child_items)
                #op, self.workingDir = ext.shell(self.fs, self.workingDir, 'ls -li')


         except IOError:
             print("Could not read device file .")

    def add_child_items(self,item, column):

        if column == 0:
            item_text = item.text(column)
            d_text = item.text(2)

            item_text = item_text[:len(item_text)-1]
            if d_text[0] == 'd':
                with self.fs:
                    #self.workingDir = self.fs.rootDir
                    op, self.workingDir = ext.shell(self.fs, self.workingDir, 'cd {0}'.format(item_text))
                    op, self.workingDir = ext.shell(self.fs, self.workingDir, 'ls -li')
                    #print(op)
                    #root = QTreeWidgetItem(item)
                    for i in op:
                        new_child = QTreeWidgetItem(i)
                        item.addChild(new_child)








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

    # def on_item_clicked(self, item, column):
    #     if column == 0:
    #         item_text = item.text(column)
    #         item_text = item_text[:len(item_text)-1]
    #         with self.fs:
    #             op, self.workingDir = ext.shell(self.fs, self.workingDir, 'cd {0}'.format(item_text))
    #             op, self.workingDir = ext.shell(self.fs, self.workingDir, 'ls -li')
    #             for i in op:
    #                 child_item = QTreeWidgetItem(i)
    #                 self.ui.treeWidget.item1.addChild(child_item)



                # print(op)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.root_item()
    sys.exit(app.exec_())
else:
	print(__name__, "Something is very wrong")


