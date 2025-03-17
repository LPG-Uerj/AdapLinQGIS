import sys

from PyQt5.QtCore import *
from PyQt5.QtGui import *

from .composite_dialog import CompositeDialog

class compositeView(CompositeDialog):
	"""docstring for compositeView"""
	def __init__(self, parent=None):

		super(compositeView, self).__init__(parent)

	def setLayersCombo(self, layersNamesList):
		""" set the names of the layers in the combo box. """
		self.rasterComboBox.clear()
		self.rasterComboBox.addItems(layersNamesList)

	def setBandsCombos(self, bandsList):
		""" set the names of the bands in the combo box. """

		self.redComboBox.clear()
		self.greenComboBox.clear()
		self.blueComboBox.clear()

		self.redComboBox.addItems(bandsList)
		self.greenComboBox.addItems(bandsList)
		self.blueComboBox.addItems(bandsList)

	def getLayerIndex(self):
		""" get the index of the raster layer in the combo box. """
		return self.rasterComboBox.currentIndex()

	def getBands(self, bandsList):

		return (bandsList[self.redComboBox.currentIndex()], bandsList[self.greenComboBox.currentIndex()], bandsList[self.blueComboBox.currentIndex()])

	def showDialog(self):

		self.show()

		return self.exec_()