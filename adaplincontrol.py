import sys
import os

# Import the PyQt and the QGIS libraries
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *

from qgis.core import *
from qgis.gui import *
import qgis.utils
from qgis.core.contextmanagers import qgisapp

# Initialize Qt resources from file resources.py
from . import resources

# Import own classes and tools
from .adaplin import Adaplin

# Import code for settings
from .settings_dialog import SettingsDialog
from .utils import *

from .compositeControl import compositeControl
from .settingsControl import settingsControl


class AdaplinControl():

    def __init__(self, iface):
        
        self.iface = iface
        self.canvas = self.iface.mapCanvas()

        self.adaplin = None

        self.currenteLayer = None

    def initGui(self):
        
        # setup action

        path = os.path.dirname(os.path.abspath(__file__))

        self.action = QAction(QIcon(path + "/AdaplinIcon.png"), "AdapLin", self.iface.mainWindow())
        
        self.action.setEnabled(False)
        self.action.setCheckable(True)
        self.action.setChecked(False)

        self.iface.addToolBarIcon(self.action)

        # triggers

        self.iface.currentLayerChanged['QgsMapLayer*'].connect(self.toggle)
        self.action.triggered.connect(self.run)
    
    def toggle(self):

        self.currenteLayer = self.canvas.currentLayer()

        if (self.currenteLayer is not None):
            
            if (self.currenteLayer.type() == QgsMapLayer.VectorLayer and self.currenteLayer.geometryType() == QgsWkbTypes.GeometryType.LineGeometry):

                try:
                    self.currenteLayer.editingStarted.disconnect(self.toggle)
                except Exception as exp:
                    pass
                try:
                    self.currenteLayer.editingStopped.disconnect(self.toggle)
                except Exception as exp:
                    pass

                if self.currenteLayer.isEditable():
                    self.action.setEnabled(True)
                    self.action.setChecked(False)
                    self.currenteLayer.editingStopped.connect(self.toggle)

                else:
                    self.action.setEnabled(False)
                    self.action.setChecked(False)
                    self.canvas.unsetCursor()
                    self.currenteLayer.editingStarted.connect(self.toggle)

                    if (self.adaplin is not None):
                        self.canvas.unsetMapTool(self.adaplin)

    def unload(self):

        self.iface.removePluginMenu("&Adaplin", self.action)
        self.iface.removeToolBarIcon(self.action)
    
    def run(self):

        if (self.action.isChecked()):

            control = compositeControl([layer for layer in QgsProject.instance().mapLayers().values()])
            answer = control.control()

            if not answer:
                QMessageBox.information(self.iface.mainWindow(), 'Error', '<h2>There are no raster layers in the Legend Interface</h2>')
                return

            if  self.iface.mapCanvas().mapSettings().destinationCrs().isGeographic():
                QMessageBox.information(self.iface.mainWindow(), 'Error', '<h2> Please choose an On-the-Fly Projected Coordinate System</h2>')

            okPressed, rasterLayer, bands = answer

            if okPressed:
                # Activate our tool if OK is pressed
                self.adaplin = Adaplin(self.iface, rasterLayer, bands, self.action)
                self.canvas.setMapTool(self.adaplin)

        else:
            self.canvas.unsetMapTool(self.adaplin)
            self.adaplin = None