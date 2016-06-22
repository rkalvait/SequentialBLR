import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *

def window():
   app = QtGui.QApplication(sys.argv)
   w = QtGui.QWidget()

   '''
   b = QtGui.QLabel(w)
   b.setText("Hello World!")
   w.setGeometry(100,100,200,50)
   b.move(50,20)
   '''

   w.setWindowTitle("Hello world!")
   w.show()
   sys.exit(app.exec_())
	
if __name__ == '__main__':
   window()