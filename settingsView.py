import sys

from PyQt5.QtCore import *
from PyQt5.QtGui import *

from .utils import *

from .settings_dialog import SettingsDialog

class settingsView(SettingsDialog):
	"""docstring for settingsView"""
	def __init__(self, parent=None):

		super(settingsView, self).__init__(parent)

		self.RestoreDefaultButton.clicked.connect(self.standardValue)

	def getValues(self):

		info1 = self.StrideDoubleSpinBox.value()
		info2 = self.VerticesSpinBox.value()
		info3 = self.SnapperDistanceDoubleSpinBox.value()
		info4 = self.SnapperModeComboBox.currentIndex()

		return (info1, info2, info3, info4)

	def setValues(self, info):

		self.StrideDoubleSpinBox.setValue(info[0])
		self.VerticesSpinBox.setValue(info[1])
		self.SnapperDistanceDoubleSpinBox.setValue(info[2])
		self.SnapperModeComboBox.setCurrentIndex(info[3])

	def showDialog(self):

		self.show()

		return self.exec_()

	def standardValue(self):

		self.StrideDoubleSpinBox.setValue(DEFAULT_STRIDE)
		self.VerticesSpinBox.setValue(DEFAULT_VERTICES)
		self.SnapperDistanceDoubleSpinBox.setValue(DEFAULT_SNAPPER_DISTANCES)
		self.SnapperModeComboBox.setCurrentIndex(DEFAULT_SNAPPER_MODE)