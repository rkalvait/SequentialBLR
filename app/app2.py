import sys
from PyQt4 import QtGui, QtCore


class Window(QtGui.QMainWindow):

    def __init__(self):
        super(Window, self).__init__()
        self.setGeometry(50, 50, 500, 300)
        self.setWindowTitle('My PyQt Application')
        self.setWindowIcon(QtGui.QIcon('merit_icon.ppm'))
        self.statusBar()
        self.menu()
        self.home()
        self.show()

    def menu(self):
        extractAction = QtGui.QAction("&GET TO THE CHOPPER", self)
        extractAction.setShortcut("Ctrl+Q")
        extractAction.setStatusTip("Leave the app")
        extractAction.triggered.connect(self.close_application)
        
        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('&File')
        fileMenu.addAction(extractAction)

        
    def home(self):
        close_button = QtGui.QPushButton("Quit", self)
        close_button.clicked.connect(self.close_application)
        close_button.resize(close_button.sizeHint())
        close_button.move(100, 100)
        
        extractAction = QtGui.QAction(QtGui.QIcon('merit_icon.ppm'), 'Close', self)
        extractAction.triggered.connect(self.close_application)
        
        self.toolBar = self.addToolBar("Extraction")
        self.toolBar.addAction(extractAction)
        
        
        
    def close_application(self):
        print("Closing down")
        sys.exit()
        
def main():
    app = QtGui.QApplication(sys.argv)
    toplevel = Window()
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()