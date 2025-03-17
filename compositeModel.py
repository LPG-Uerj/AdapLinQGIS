import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qgis.core import *
from qgis.gui import *
import qgis.utils
from qgis.core.contextmanagers import qgisapp

class compositeModel():
    """ model class for the composite definition. """
    def __init__(self, layers):

        self.layers = layers
       
    def parseRasterLayers(self):
        """ Get all raster layers from the current project. """

        self.rasterLayers = []
        RasterExists = False
        
        for layer in self.layers:
            if layer.type() == QgsMapLayer.RasterLayer:
                self.rasterLayers.append(layer)
                RasterExists = True

        return RasterExists


    def getRasterLayers(self):
        """ return a list with all raster layers in the current project. """

        return self.rasterLayers


    def getRasterNamesList(self):
        """ return a list with all names of raster layers. """

        layersNamesList = [] # passivel de merda #

        for layer in self.rasterLayers:
            layersNamesList.append(layer.name())

        return layersNamesList


    def parseRasterBands(self, layerIndex):
        """ return a list with the bands of the current raster layer. """

        selectedLayer = self.rasterLayers[layerIndex]
        numBands = selectedLayer.bandCount()
        bandsList = [str(b) for b in range(1, numBands+1)]

        return bandsList