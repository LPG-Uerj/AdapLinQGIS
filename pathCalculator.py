from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qgis.core import *
from qgis.gui import *
import numpy as np
from math import sqrt
import collections

from .utils import *


class pathCalculator():

    def __init__(self, iface, pair_points, camada_raster, bandas):
        self.iface = iface
        self.pair_points = pair_points
        self.camada_raster = camada_raster
        self.bandas = bandas
        
   
    
    
    def _debug_plot_graph(self, grafo):
        # Display graph as point layer for debug
        camada_memoria = QgsVectorLayer(f"Point?crs={self.camada_raster.crs().authid()}&field=id:integer", "grafo pontos", "memory")
        
        provedor = camada_memoria.dataProvider()
        for lista_ponto in grafo:
            for ponto in lista_ponto:
                feicao = QgsFeature()
                feicao.setGeometry(QgsGeometry.fromPointXY(ponto))
                feicao.setAttributes([1])
                provedor.addFeatures([feicao])
                
                
        # camada_memoria.commitChanges()
        # camada_memoria.updateExtents()
                
        QgsProject.instance().addMapLayers([camada_memoria])

    def _debug_plot_result(self, result):
        # Display graph as point layer for debug
        camada_memoria = QgsVectorLayer(f"Point?crs={self.camada_raster.crs().authid()}&field=id:integer", "resultado grafo", "memory")
        
        provedor = camada_memoria.dataProvider()
        for ponto in result:
            feicao = QgsFeature()
            feicao.setGeometry(QgsGeometry.fromPointXY(ponto))
            feicao.setAttributes([1])
            provedor.addFeatures([feicao])
                
                
        # camada_memoria.commitChanges()
        # camada_memoria.updateExtents()
                
        QgsProject.instance().addMapLayers([camada_memoria])        

    
    # Interpolate 2 points between the segment traced by the user
    def interpolate(self, points):
        #print('----Início da Interpolação----')
    
        # Here the graph is represented by a list of lists of QgsPoint
        grafo = []                               
        
        npoints = len(points)
        
        # If there is 1 point, we will not interpolate  
        #if npoints == 1: return [QgsPoint(1,1), points[0]], grafo, [], None
        
        if npoints == 1: 
            #print('Término da Interpolação, pois só tem 1 ponto. npoints = ', npoints)
            return [QgsPoint(1,1), points[0]]
        
        
        #print('Formação do Grafo')
        # Loop in the points presented in the segment to interpolate (here npoints always will be 2, but this is designed to work even if it is passed a poliline)
        for i in range(0, npoints-1):
            #print('i igual a 0 (ponto inicial) ou 1 (ponto final). i = ', i)
            # Try to add the perpendicular lines (formed by QgsPoints) to the segment, in order to do the interpolation
            # If points are out of raster bounds or other exception occurs, we don't interpolate
            try:
                retas_perpendiculares = self.calculate_line(points[i], points[i+1])
            except Exception as e:
                #print('Exceção foi ', e)
                #return points, grafo, [], []
                return points
            
            grafo.append([points[i]])
            grafo.extend(retas_perpendiculares)
        
        grafo.append([points[-1]])
        
        # Plota gráfico na tela para debug
        #self._debug_plot_graph(grafo)
        
        # Acha caminho
        result, p = self.find_path(grafo, points)
        
        #return result, grafo, retas_perpendiculares, result
        #print('Resultado da interpolação é ', result)
        
        #self._debug_plot_result(result)
        
        return result
    
    # Calculate the points that will be candidates to the result of point interpolation
    def calculate_line(self, p1, p2):
        # Get, from Adaplin Settings, the number of points that will be above (perpendicular that is counter-clockwise) and under (perpendicular that is clockwise) in each 
        # perpendicular segment to the segment traced by the user
        # The total of points in the perpendicular line will be 2 times pontos_acima_e_abaixo (above and under) plus 1 (that is located on the segment) 
        pontos_acima_e_abaixo = int(QSettings().value(SETTINGS_NAME + "/vertices", DEFAULT_VERTICES))
        
        # Get, from Adaplin Settings, the spacement between the points in the perpendicular to the segment traced by the user 
        resolucao_y = float(QSettings().value(SETTINGS_NAME + "/stride", DEFAULT_STRIDE)) 
        
        # Calculate the unit vector (x and y coordinates)
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        
        dist = sqrt(dx*dx + dy*dy)
        
        dx /= dist # x coordinate of the unit vector
        dy /= dist # y coordinate of the unit vector
        
        # Calculate list of x coordinates (coord_x_sobre) and y coordinates (coord_y_sobre) of inserted points on the line
        x_p1 = p1.x()
        x_p2 = p2.x()
        y_p1 = p1.y()
        y_p2 = p2.y()
                
        q = 2 # number of inserted points
        n = 3.0 # number of segments originated from insertion of q points
        
        coord_x_sobre = []
        coord_y_sobre = []

        for i in range(q, 0, -1):
            coord_x_sobre.append((i/(n))*x_p1 + (1. - i/n)*x_p2) 
            coord_y_sobre.append((i/(n))*y_p1 + (1. - i/n)*y_p2) 
        
        
        # Compute retas_perpendiculares list of lists. Each list inside retas_perpendiculares will be made of 
        # QgsPoints that are the possible points to interpolate in that line perpendicular to the user segment 
        retas_perpendiculares = []
        
        for i in range(len(coord_x_sobre)):
            x_acima = [(coord_x_sobre[i] - resolucao_y*j*dy) for j in range(1,pontos_acima_e_abaixo)] # Here we subtract resolucao_y*j*dy because the unit vector perpendicular (counter-clockwise) to the unit vector (dx, dy) is (-dy, dx)
            y_acima = [(coord_y_sobre[i] + resolucao_y*j*dx) for j in range(1,pontos_acima_e_abaixo)]

            x_abaixo = [(coord_x_sobre[i] + resolucao_y*j*dy) for j in range(1,pontos_acima_e_abaixo)]
            y_abaixo = [(coord_y_sobre[i] - resolucao_y*j*dx) for j in range(1,pontos_acima_e_abaixo)]        
        
            lista_de_x = [coord_x_sobre[i]] + x_acima + x_abaixo
            lista_de_y = [coord_y_sobre[i]] + y_acima + y_abaixo
        
            lista_pontos_perpendiculares = [QgsPointXY(lista_de_x[j], lista_de_y[j]) for j in range(len(lista_de_x))]

            retas_perpendiculares.append(lista_pontos_perpendiculares)
        
        return retas_perpendiculares
    
    # Property 1: Maximize the rgb average of the poliline 
    def Prop1(self, no1, no2, no3):
        no1_media = self.average_rgb(self.camada_raster, no1)
        no2_media = self.average_rgb(self.camada_raster, no2)
        no3_media = self.average_rgb(self.camada_raster, no3)       
        
        return no1_media*no1_media + no2_media*no2_media + no3_media*no3_media
    
    # Property 2: Minimize the difference between rgb averages of the poliline     
    def Prop2(self, no1, no2, no3):
        no1no2 = self.pointsDist(no1, no2) 
        no2no3 = self.pointsDist(no2, no3) 
        
        nc_no1 = self.average_rgb(self.camada_raster, no1)
        nc_no2 = self.average_rgb(self.camada_raster, no2)
        nc_no3 = self.average_rgb(self.camada_raster, no3)
        
        mediaNo1No2 = (nc_no1 + nc_no2)/2.
        mediaNo2No3 = (nc_no2 + nc_no3)/2.
        
        somatorio_Prop2 = ((nc_no1 - mediaNo1No2)*(nc_no1 - mediaNo1No2) + (nc_no2 - mediaNo1No2)*(nc_no2 - mediaNo1No2)) + ((nc_no2 - mediaNo2No3)*(nc_no2 - mediaNo2No3) + (nc_no3 - mediaNo2No3)*(nc_no3 - mediaNo2No3)) 
        
        return somatorio_Prop2

    # Property 3: Minimize the poliline curvature     
    def Prop3(self, no1, no2, no3):
        no1no2 = self.pointsDist(no1, no2) 
        no2no3 = self.pointsDist(no2, no3) 
        no1no3 = self.pointsDist(no1, no3)
        distTotal = no1no2 + no2no3
        
        cosseno_interno = ( (no1no2*no1no2 + no2no3*no2no3 - no1no3*no1no3) / (2*no1no2*no2no3) ) 
        cosseno_deflexao = -1*cosseno_interno
        
        return (1 + cosseno_deflexao) /no1no2
    
    # Calculate the average of the input bands in the pixel corresponding to the point of interest    
    def average_rgb(self, raster, ponto):
        provedor = raster.dataProvider()        

        # We have to transform the point to the raster projection
        mapCanvasSrs = self.iface.mapCanvas().mapSettings().destinationCrs()
        rasterSrs = raster.crs()
        srsTransform = QgsCoordinateTransform(mapCanvasSrs, rasterSrs, QgsProject.instance())
        
        ponto_transform = srsTransform.transform(ponto)
        ponto_valor = provedor.identify(ponto_transform, QgsRaster.IdentifyFormatValue).results()
        
        if len(ponto_valor) > 3:
            ponto_media = sum([ponto_valor[i] for i in [int(self.bandas[0]), int(self.bandas[1]), int(self.bandas[2])]])/3.
        else:
            ponto_media = sum([ponto_valor[i] for i in ponto_valor])/float(len(ponto_valor))
        
        return ponto_media        
    
 
    
    # This function gives the best path in a graph considering the objective function that takes in consideration the properties Prop1, Prop2 and Prop3 
    def find_path(self, grafo, points):
        #print('----Início da função que Acha Caminho----')
        
        def maximum(dic):
            for elem in dic:
                if elem == 'MAX':
                    continue
                if dic[elem] == dic['MAX']:
                    return elem
                    
        # We begin with an empty list of dictionaries            
        lista_dic = []
        lista_dic.append({})
        
        no_inicial = grafo[0][0]
        #print('Nó inicial = ', no_inicial, type(no_inicial))
        
        # Dictionaries list with the first edges of the graph
        for no in grafo[1]:
            # lista_dic[0][(frozenset(no_inicial), frozenset(no))] = {'MAX': 0} #lista_dic[0][frozenset(no_inicial, no)] = {'MAX': 0}
            lista_dic[0][(no_inicial, no)] = {'MAX': 0} 
        
        # Use dynamic programming to calculate the MAX cost of the paths from the initial to the final vertex
        for i in range(len(grafo)):
            g = grafo[i]

            try:
                g_k_mais_dois = grafo[i+2]
            except:
                break
        
            g_k_mais_um = grafo[i+1]
            lista_dic.append({})
        
            for j in range(len(g_k_mais_um)):
                for k in range(len(g_k_mais_dois)):
                    no_k_mais_um = g_k_mais_um[j]
                    no_k_mais_dois = g_k_mais_dois[k]
                                        
                    lista_dic[i+1][(no_k_mais_um, no_k_mais_dois)] = {}
                                        
                    for z in range(len(g)):
                        no_atual = g[z] 
                        
   
                        try:                                            
                            res_parcial = lista_dic[i][(no_atual, no_k_mais_um)]['MAX'] + (self.Prop1(no_atual, no_k_mais_um, no_k_mais_dois) - self.Prop2(no_atual, no_k_mais_um, no_k_mais_dois))*self.Prop3(no_atual, no_k_mais_um, no_k_mais_dois)
                        except Exception as e:
                            #print('Exceção foi ', e)
                            return points, points                             
                        
                        lista_dic[i+1][(no_k_mais_um, no_k_mais_dois)][no_atual] = res_parcial
                                            

                    lista_dic[i+1][(no_k_mais_um, no_k_mais_dois)]['MAX'] = max([lista_dic[i+1][(no_k_mais_um, no_k_mais_dois)][el] for el in lista_dic[i+1][(no_k_mais_um, no_k_mais_dois)]])
                    

        lista_dic_inv = lista_dic[-1:0:-1] 
        prima = lista_dic_inv[0]
        
        ultimos, f_acum, no_escolhido = max([(chave, valor['MAX'], maximum(valor)) for chave, valor in prima.items()], key = lambda par_facum: par_facum[1])
        no_anterior, no_posterior = ultimos 
    
        caminho = []
        caminho += (no_posterior, no_anterior, no_escolhido)
    
        for elemento in lista_dic_inv[1::]:
            no_posterior, no_anterior = no_anterior, no_escolhido
            no_escolhido = maximum(elemento[(no_anterior, no_posterior)])
            caminho.append(no_escolhido)
        
        caminho.reverse()
    
        return caminho, points
    
    # Calculate the euclidean distance between 2 points
    def pointsDist(self, a, b):
        dx = a.x()-b.x()
        dy = a.y()-b.y()
        return sqrt( dx*dx + dy*dy )
