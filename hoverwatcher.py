from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qgis.core import *
from qgis.gui import *

class HoverWatcher(QObject):
    hoverEnter = pyqtSignal()
    hoverLeave = pyqtSignal()
    
    def __init__(self, parent):
        QObject.__init__(self)
        self._parent = parent
        self._parent.installEventFilter(self)

    def eventFilter(self, object, event):
        if not (object is self._parent):
            return False
        elif event.type() == QEvent.Enter:
            self.hoverEnter.emit()
            return True
        elif event.type() == QEvent.Leave:
            self.hoverLeave.emit()
            return True
        else:
            return False

    def __del__(self):
        while True:
            try:
                self.hoverEnter.disconnect()
            except TypeError:
                break
        while True:
            try:
                self.hoverLeave.disconnect()
            except TypeError:
                break
        self._parent.removeEventFilter(self)
        