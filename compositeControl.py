import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qgis.core import *
from qgis.gui import *
import qgis.utils
from qgis.core.contextmanagers import qgisapp

from .compositeModel import compositeModel
from .compositeView import compositeView

class compositeControl():
	"""docstring for compositeControl"""
	def __init__(self,layers):

		self.model = compositeModel(layers)
		self.view = compositeView()

		self.view.rasterComboBox.currentIndexChanged.connect(self.slot1)

	def slot1(self):

		self.view.setBandsCombos(self.model.parseRasterBands(self.view.getLayerIndex()))

	def control(self):

		RasterExists = self.model.parseRasterLayers()

		if not (RasterExists): return 0 # Retornar um touple (0,0,0) #

		self.view.setLayersCombo(self.model.getRasterNamesList())
		self.view.setBandsCombos(self.model.parseRasterBands(self.view.getLayerIndex()))

		okPressed = self.view.showDialog()
		

		bands = self.view.getBands(self.model.parseRasterBands(self.view.getLayerIndex()))
		layer = self.model.rasterLayers[self.view.getLayerIndex()]

		return (okPressed, layer, bands)


