from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import *
from qgis.gui import *

from .utils import *
from .pathCalculator import *
from .hoverwatcher import HoverWatcher

class Adaplin(QgsMapTool):

    def __init__(self, iface, camada_raster, bandas, action):  

        self.camada_raster = camada_raster
        self.iface = iface
        self.action = action
        self.canvas = self.iface.mapCanvas()
        self.bandas = bandas

        super().__init__(self.canvas)
        self.rb = QgsRubberBand(self.canvas,  QgsWkbTypes.GeometryType.PolygonGeometry)
        self.type = QgsWkbTypes.GeometryType.PolygonGeometry
        
        color = QColor(255,0,0,100)
        self.rb.setColor(color)
        self.rb.setWidth(5)

        self.vertex_markers = []

        self.points = []
        self.pontos_interpolados = []
        self.mCtrl = False

        self.isPolygon = False
        self.type = None

        self.canvas_hover_watcher = HoverWatcher(self.canvas)
        self.canvas_hover_watcher.hoverLeave.connect(self.canvasMoveOut)

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
     
    def activate(self):

        self.canvas.setCursor(self.cursor)
        
        self.type = self.canvas.currentLayer().geometryType()
        
        if self.type == QgsWkbTypes.GeometryType.PolygonGeometry:
            self.isPolygon = True
    
    def deactivate(self):

        if (len(self.points) >= 2):
            self.createFeature(self.pontos_interpolados)

        self.resetPoints()
        self.resetRubberBand()
        self.canvas_hover_watcher.__del__()
        self.canvas.refresh()
        QgsMapTool.deactivate(self)

    def canvasPressEvent(self, event):
        
        if (event.button() == Qt.LeftButton):
        
            point = self.canvas.getCoordinateTransform().toMapCoordinates(event.pos())
            self.points.append(point)
        
            if (self.mCtrl):
                self.pontos_interpolados.append(point)

            else:
                pontos_recentes = self.interpolation(self.points[-2::])
                self.pontos_interpolados = self.pontos_interpolados + pontos_recentes[1:]
   
            self.setRubberBandPoints(self.pontos_interpolados)

        elif (event.button() == Qt.RightButton):
            if (len(self.points) >= 2):
                self.createFeature(self.pontos_interpolados)

            self.resetRubberBand()
            self.resetPoints()
            self.canvas.refresh()

    def canvasMoveEvent(self,event):

        point = self.canvas.getCoordinateTransform().toMapCoordinates(event.pos())
        
        pontos_marcados = [i for i in self.points] + [point]
        pontos_interpolados = [i for i in self.pontos_interpolados]
        
        if self.mCtrl:
            pontos_interpolados.append(point)
        else:
            pontos_recentes = self.interpolation(pontos_marcados[-2::])
            pontos_interpolados = pontos_interpolados + pontos_recentes[1:]
              
        self.setRubberBandPoints(pontos_interpolados)

    def keyPressEvent(self,  event):

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

        # if event.key() == Qt.Key_Backspace:
        if event.key() == 45: # key 45 = "-"
            self.removeLastPoint()

    def setRubberBandPoints(self,points):

        self.resetRubberBand()

        for point in points:

            update = point is points[-1]
            self.rb.addPoint(point, update)
                        
            m = QgsVertexMarker(self.canvas)
            m.setCenter(point)
            m.setColor(QColor(0, 0, 0))
            m.setIconSize(5)
            m.setIconType(QgsVertexMarker.ICON_BOX)
            m.setPenWidth(3)

            self.vertex_markers.append(m)

    def createFeature(self, pontos_interpolados):

        layer = self.canvas.currentLayer() 
        provider = layer.dataProvider()
        fields = layer.fields()
        f = QgsFeature(fields)
            
        coords = pontos_interpolados
        
        if (layer.crs() != self.canvas.mapSettings().destinationCrs()):
            coords_tmp = [i for i in coords]
            coords = []
            for point in coords_tmp:
                transformedPoint = self.canvas.mapSettings().mapToLayerCoordinates(layer, point)
                coords.append(transformedPoint)
              
        if (self.isPolygon):
            g = QgsGeometry().fromPolygon([coords])
        else:
            g = QgsGeometry().fromPolylineXY(coords)
        f.setGeometry(g)
            
        for field in fields.toList():
            ix = fields.indexFromName(field.name())
            f[field.name()] = provider.defaultValue(ix)

        layer.beginEditCommand("Feature added")
        
        settings = QSettings()
        
        if (len(self.points) != 0):
            disable_attributes = settings.value( "/qgis/digitizing/disable_enter_attribute_values_dialog", False, type=bool)

            if disable_attributes:
                layer.addFeature(f)
                layer.endEditCommand()
            else:
                dlg = self.iface.getFeatureForm(layer, f)
                dlg.setMode(True) 
                if (dlg.exec_()):
                    layer.endEditCommand()
                else:
                    layer.destroyEditCommand()
                    
        else:
            QMessageBox.information(self.iface.mainWindow(), 'Warning', 'No points marked yet')

    def interpolation(self, points):

        grafo = pathCalculator(self.iface, points, self.camada_raster, self.bandas)
        
        return grafo.interpolate(points)
    
    def resetPoints(self):

        self.points.clear()
        self.pontos_interpolados.clear()
        # self.vertex_markers.clear()

    def resetRubberBand(self):

        self.rb.reset(self.type)

        for i in reversed(range(len(self.vertex_markers))):
            self.canvas.scene().removeItem(self.vertex_markers[i])
            del self.vertex_markers[i]
        
    def removeLastPoint(self):

        if len(self.points) == 0:
            QMessageBox.information(self.iface.mainWindow(), 'Worning', 'No points marked yet')
        elif len(self.points) == 1:
            self.points.pop()
            self.pontos_interpolados.pop()
        else:
            penultimo_elemento_marcado = self.points[-2]
            self.pontos_interpolados = self.pontos_interpolados[0:self.pontos_interpolados.index(penultimo_elemento_marcado)+1]
            self.points.pop()

    def canvasMoveOut(self):
        i = -1
        self.rb.reset(self.type)
        self.canvas.scene().removeItem(self.vertex_markers[i])
        del self.vertex_markers[i]