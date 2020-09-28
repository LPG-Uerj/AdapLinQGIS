# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
import numpy as np
from math import sqrt
import collections

from utils import *
from pathCalculator import *


class Adaplin(QgsMapTool):

    """ 
    Adaplin Plugin Class

        Implements the optimal path based on properties 1, 2 and 3.
        Prop1: Models the road considering that its spectral answer is superior to that of the surroundings;
        Prop2: Reflects the homogeneity of the spectral answer of the road;
        Prop3: Regularization term of the shape of the road, aiming a smoother curvature.

        Each time the user moves the mouse, a preview of the road is rendered. When the user clicks, the preview
        is inserted in the polyline.

        More information: http://www.seer.ufu.br/index.php/revistabrasileiracartografia/article/view/45398
    """

    def __init__(self, iface, camada_raster, bandas, action):
        self.camada_raster = camada_raster
        self.iface = iface
        self.action = action
        self.canvas = self.iface.mapCanvas()
        self.bandas = bandas
        
        QgsMapTool.__init__(self, self.canvas)
        self.rb = QgsRubberBand(self.canvas,  QGis.Polygon)
        self.type = QGis.Polygon 
        
        # List of points (points) marked by the user, of all the points that will form the line (pontos_interpolados) 
        # and variable to set the manual mode ON or OFF (at start is OFF)
        self.points = []
        self.pontos_interpolados = []
        self.mCtrl = False

        self.cursor = QCursor(QPixmap(["16 16 3 1",
                                      "      c None",
                                      ".     c #FF0000",
                                    
                                    
                                      "+     c #FFFFFF",
                                      "                ",
                                      "       +.+      ",
                                      "      ++.++     ",
                                      "     +.....+    ",
                                      "    +.     .+   ",
                                      "   +.   .   .+  ",
                                      "  +.    .    .+ ",
                                      " ++.    .    .++",
                                      " ... ...+... ...",
                                      " ++.    .    .++",
                                      "  +.    .    .+ ",
                                      "   +.   .   .+  ",
                                      "   ++.     .+   ",
                                      "    ++.....+    ",
                                      "      ++.++     ",
                                      "       +.+      "]))       
                                      
    def canvasPressEvent(self, event):

        """ If the selected layer is editable and adaplin is selected, it interpolates the path between the last point
        present in the polyline and the coordinate of the mouse click. All new points are added to the polyline. """

        layer = self.canvas.currentLayer()

        if layer.isEditable() and self.action.isChecked():
            # Device coordinates of mouse
            x = event.pos().x()
            y = event.pos().y()
            
            # Add the marked point on left click
            if event.button() == Qt.LeftButton:
                startingPoint = QPoint(x,y) 
                
                # Try to snap to current Layer if it is specified in QGIS digitizing options
                snapper = QgsMapCanvasSnapper(self.canvas)
                (retval,result) = snapper.snapToCurrentLayer (startingPoint, QgsSnapper.SnapToVertex)
                     
                if result != []:
                    point = QgsPoint( result[0].snappedVertex )
                else:
                    (retval,result) = snapper.snapToBackgroundLayers(startingPoint)
                    if result != []:
                        point = QgsPoint( result[0].snappedVertex )
                    else:
                        point = self.canvas.getCoordinateTransform().toMapCoordinates( event.pos().x(), event.pos().y() )
                
                # Append point to list of points marked by the user
                self.points.append(point)
                
                # If tool is in Manual Mode, we just append the point to pontos_interpolados            
                if self.mCtrl:
                    self.pontos_interpolados.append(point)
                # If the tool is in Default Mode, we append the new points to pontos_interpolados
                else:
                    pontos_recentes = self.interpolation ( self.points[-2::] )
                    self.pontos_interpolados = self.pontos_interpolados + pontos_recentes[1:] 
            
            # On the right click, we create the feature with pontos_interpolados and clear the things for the next feature  
            else:
                if len( self.points ) >= 2:
                    self.createFeature(self.pontos_interpolados) 

                self.resetPoints()
                self.resetRubberBand()
                self.canvas.refresh()

    def resetPoints(self):

        """ Reset the list points e pontos_interpolados. """

        self.points = []
        self.pontos_interpolados = []
    
    def createFeature(self, pontos_interpolados):

        """ Insert a poliline into current layer shapefile. """

        layer = self.canvas.currentLayer() 
        provider = layer.dataProvider()
        fields = layer.pendingFields()
        f = QgsFeature(fields)
            
        coords = pontos_interpolados
        
        if self.canvas.mapSettings().hasCrsTransformEnabled() and layer.crs() != self.canvas.mapSettings().destinationCrs():
            coords_tmp = coords[:]
            coords = []
            for point in coords_tmp:
                transformedPoint = self.canvas.mapSettings().mapToLayerCoordinates( layer, point )
                coords.append(transformedPoint)
              
        if self.isPolygon == True:
            g = QgsGeometry().fromPolygon([coords])
        else:
            g = QgsGeometry().fromPolyline(coords)
        f.setGeometry(g)
            
        for field in fields.toList():
            ix = fields.indexFromName(field.name())
            f[field.name()] = provider.defaultValue(ix)

        layer.beginEditCommand("Feature added")
        
        settings = QSettings()
        
        if len(self.points) != 0:
            disable_attributes = settings.value( "/qgis/digitizing/disable_enter_attribute_values_dialog", False, type=bool)

            if disable_attributes:
                layer.addFeature(f)
                layer.endEditCommand()
            else:
                dlg = self.iface.getFeatureForm(layer, f)
                if QGis.QGIS_VERSION_INT >= 20400: 
                    dlg.setMode( True ) 
                if dlg.exec_():
                    if QGis.QGIS_VERSION_INT < 20400: 
                        layer.addFeature(f)
                    layer.endEditCommand()
                else:
                    layer.destroyEditCommand()

        else:
            QMessageBox.information(self.iface.mainWindow(), 'Aviso', 'Nenhum ponto marcado ainda')
            return
    
    def canvasMoveEvent(self,event):

        """ Trigged whenever the user moves the mouse, redrawing the preview of the road. """

        color = QColor(255,0,0,100)
        self.rb.setColor(color)
        self.rb.setWidth(3)

        x = event.pos().x()
        y = event.pos().y()
        
        startingPoint = QPoint(x,y)
        snapper = QgsMapCanvasSnapper(self.canvas)
            
        (retval,result) = snapper.snapToCurrentLayer (startingPoint, QgsSnapper.SnapToVertex)   
        if result != []:
            point = QgsPoint(result[0].snappedVertex)
        else:
            (retval,result) = snapper.snapToBackgroundLayers(startingPoint)
            if result != []:
                point = QgsPoint(result[0].snappedVertex)
            else:
                point = self.canvas.getCoordinateTransform().toMapCoordinates(event.pos().x(), event.pos().y());
        
        pontos_marcados = list(self.points)
        pontos_interpolados = list(self.pontos_interpolados)
        pontos_marcados.append(point)
        
        if self.mCtrl:
            pontos_interpolados.append(point)
        else:
            #pontos_recentes, grafo, pontos_perpendiculares, result = self.interpolation ( pontos_marcados[-2::] )
            pontos_recentes = self.interpolation (pontos_marcados[-2::])
            pontos_interpolados = pontos_interpolados + pontos_recentes[1:]
       
        self.setRubberBandPoints(pontos_interpolados)

    def activate(self):

        """ Verify if the selected layer is QGis.Polygon type. If true, self.isPolygon = True. """

        self.canvas.setCursor(self.cursor)
        
        layer = self.canvas.currentLayer()
        self.type = layer.geometryType()
        self.isPolygon = False
        if self.type == QGis.Polygon:
            self.isPolygon = True
            
    def resetRubberBand(self):

        """ Reset rubber bands list. """

        self.rb.reset(self.type)

    def setRubberBandPoints(self,points):

        self.resetRubberBand()
        for point in points:
            update = point is points[-1]
            self.rb.addPoint(point, update)

    # 
    def interpolation(self, points):

        """ Calculate the optimal path based at the obtained points in canvasPressEvent(). 
            Interpolate 2 points between the segment traced by the user. """
        
        grafo = pathCalculator(self.iface, points, self.camada_raster, self.bandas)
        
        # Do the interpolation
        pontos_recentes = grafo.interpolation(points)

        return pontos_recentes

    def keyPressEvent(self,  event):

        """ 
        Switch the tool state:
        Ctrl: Enable or Disable the optimal path;
        Esc: Ends the feature;
        Shift: Center the mapcanvas in the last clicked point.

        """

        if event.key() == Qt.Key_Control:
            if self.mCtrl is True:
                self.mCtrl = False
            else:
                self.mCtrl = True
        if event.key() == Qt.Key_Escape:
            self.createFeature(self.pontos_interpolados)
            self.resetPoints()
            self.resetRubberBand()
            self.canvas.refresh()
        if event.key() == Qt.Key_Shift:
            try:
                ultimo_ponto = self.pontos_interpolados[-1]
                self.canvas.setExtent(QgsRectangle(ultimo_ponto, ultimo_ponto))
                self.canvas.refresh()
            except:
                pass

    def keyReleaseEvent(self,  event):

        """ Enabled when user presses BackSpace. Delete the last point added. """

        if event.key() == Qt.Key_Backspace:
            self.removeLastPoint()

    def removeLastPoint(self):

        """ Removes the last point from the list points and pontos_interpolados. """

        if len(self.points) == 0:
            QMessageBox.information(self.iface.mainWindow(), 'Aviso', 'Nenhum ponto marcado ainda')
        elif len(self.points) == 1:
            self.points.pop()
            self.pontos_interpolados.pop()
        else:
            penultimo_elemento_marcado = self.points[-2]
            self.pontos_interpolados = self.pontos_interpolados[0:self.pontos_interpolados.index(penultimo_elemento_marcado)+1]
            self.points.pop()
