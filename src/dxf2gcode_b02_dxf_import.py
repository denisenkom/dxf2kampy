#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_b02_dxf_import
#Programmer: Christian Kohloeffel
#E-mail:     n/A
#
#Copyright 2008 Christian Kohloeffel
#
#Distributed under the terms of the GPL (GNU Public License)
#
#dxf2gcode is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 2 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


from dxf2gcode_b02_point import PointClass, PointsClass, ContourClass

from dxf2gcode_b02_geoent_arc import ArcClass
from dxf2gcode_b02_geoent_circle import CircleClass
from dxf2gcode_b02_geoent_insert import InsertClass
from dxf2gcode_b02_geoent_line import LineClass
from dxf2gcode_b02_geoent_polyline import PolylineClass
from dxf2gcode_b02_geoent_spline import SplineClass
from dxf2gcode_b02_geoent_ellipse import EllipseClass
from dxf2gcode_b02_geoent_lwpolyline import LWPolylineClass

import sys, os
from Tkconstants import END
from tkMessageBox import showwarning
from Canvas import Oval, Arc, Line
from copy import deepcopy, copy
from string import find, strip
from math import sqrt, sin, cos, atan2, radians, degrees

class Load_DXF:
    #Initialisierung der Klasse
    def __init__(self, filename=None,config=None,textbox=None):

        self.textbox=textbox
        self.config=config        

        #Laden der Kontur und speichern der Werte in die Klassen  
        str=self.Read_File(filename)

        self.line_pairs=self.Get_Line_Pairs(str)        

        #Debug Informationen 
        self.textbox.prt(("\n\nFile has   %0.0f Lines" %len(str)),1)
        self.textbox.prt(("\nFile has   %0.0f Linepairs" %self.line_pairs.nrs),1)

        sections_pos=self.Get_Sections_pos()
        self.layers=self.Read_Layers(sections_pos)

        blocks_pos=self.Get_Blocks_pos(sections_pos)
        self.blocks=self.Read_Blocks(blocks_pos)
        self.entities=self.Read_Entities(sections_pos)

        #Aufruf der Klasse um die Konturen zur suchen
        #Schleife f�r die Anzahl der Bl�cke und den Layern
        for i in range(len(self.blocks.Entities)):
            # '\n'
            #print self.blocks.Entities[i]
            self.blocks.Entities[i].cont=self.Get_Contour(self.blocks.Entities[i])

        self.entities.cont=self.Get_Contour(self.entities)
   
    #Laden des ausgew�hlten DXF-Files
    def Read_File(self,filename ):
        file = open(filename,'r')
        str = file.readlines()
        file.close()
        return str
    
    #Die Geladenene Daten in Linien Pare mit Code & Value umwandeln.
    def Get_Line_Pairs(self,str):
        line=0
        line_pairs=dxflinepairsClass([])
        #Start bei der ersten SECTION
        while (find(str[line],"SECTION")<0):
            line+=1
        line-=1

        #Durchlauf bis zum Ende falls kein Fehler auftritt. Ansonsten abbruch am Fehler
        try:
            while line < len(str):
                line_pairs.line_pair.append(dxflinepairClass(int(strip(str[line])),strip(str[line+1])))
                line+=2

        except:
            
            showwarning("Warning reading linepairs",("Failure reading line stopped at line %0.0f.\n Please check/correct line in dxf file" %(line)))
            self.textbox.prt(("\n!Warning! Failure reading lines stopped at line %0.0f.\n Please check/correct line in dxf file\n " %(line)))
            
            
        line_pairs.nrs=len(line_pairs.line_pair)
        return line_pairs
        
    #Suchen der Sectionen innerhalb des DXF-Files n�tig um Bl�cke zu erkennen.
    def Get_Sections_pos(self):
        sections=[]
        
        start=self.line_pairs.index_both(0,"SECTION",0)

        #Wenn eine Gefunden wurde diese anh�ngen        
        while (start != None):
            #Wenn eine Gefunden wurde diese anh�ngen
            sections.append(SectionClass(len(sections)))
            sections[-1].begin=start
            name_pos=self.line_pairs.index_code(2,start+1)
            sections[-1].name=self.line_pairs.line_pair[name_pos].value
            end=self.line_pairs.index_both(0,"ENDSEC",start+1)
            #Falls Section nicht richtig beendet wurde
            if end==None:
                end=self.line_pairs.nrs-1
                
            sections[-1].end=end
            
            start=self.line_pairs.index_both(0,"SECTION",end)
            
        self.textbox.prt(("\n\nSections found:" ),1)
        for sect in sections:
            self.textbox.prt(str(sect),1)
                
        return sections

    #Suchen der TABLES Section innerhalb der Sectionen diese beinhaltet die LAYERS
    def Read_Layers(self,section):
        layer_nr=-1
        for sect_nr in range(len(section)):
            if(find(section[sect_nr].name,"TABLES") == 0):
                tables_section=section[sect_nr]
                break

        #Falls das DXF Bloecke hat diese einlesen
        layers=[]
        if vars().has_key('tables_section'):
            tables_section=section[sect_nr]
            start=tables_section.begin
            
            while (start != None):
                start=self.line_pairs.index_both(0,"LAYER",start+1,tables_section.end)
                if(start != None):
                    start=self.line_pairs.index_code(2,start+1)
                    layers.append(LayerClass(len(layers)))
                    layers[-1].name=self.line_pairs.line_pair[start].value
                    
        self.textbox.prt(("\n\nLayers found:" ),1)
        for lay in layers:
            self.textbox.prt(str(lay),1)
            
        return layers
                    
            
    #Suchen der BLOCKS Section innerhalb der Sectionen
    def Get_Blocks_pos(self,section):
        for sect_nr in range(len(section)):
            if(find(section[sect_nr].name,"BLOCKS") == 0):
                blocks_section=section[sect_nr]
                break

        #Falls das DXF Bloecke hat diese einlesen
        blocks=[]
        if vars().has_key('blocks_section'):
            start=blocks_section.begin
            start=self.line_pairs.index_both(0,"BLOCK",blocks_section.begin,blocks_section.end)
            while (start != None):
                blocks.append(SectionClass())
                blocks[-1].Nr=len(blocks)
                blocks[-1].begin=start
                name_pos=self.line_pairs.index_code(2,start+1,blocks_section.end)
                blocks[-1].name=self.line_pairs.line_pair[name_pos].value
                end=self.line_pairs.index_both(0,"ENDBLK",start+1,blocks_section.end)
                blocks[-1].end=end
                start=self.line_pairs.index_both(0,"BLOCK",end+1,blocks_section.end)

        self.textbox.prt(("\n\nBlocks found:" ),1)
        for bl in blocks:
            self.textbox.prt(str(bl),1)
            
        return blocks

    #Lesen der Blocks Geometrien
    def Read_Blocks(self,blocks_pos):
        blocks=BlocksClass([])
        warning=0
        for block_nr in range(len(blocks_pos)):
            self.textbox.prt(("\n\nReading Block Nr: %0.0f" % block_nr ),1)
            blocks.Entities.append(EntitiesClass(block_nr,blocks_pos[block_nr].name,[]))
            #Lesen der BasisWerte f�r den Block
            s=blocks_pos[block_nr].begin+1
            e=blocks_pos[block_nr].end-1
            lp=self.line_pairs
            #XWert
            pos=lp.index_code(10,s+1,e)
            if pos:
                blocks.Entities[-1].basep.x=float(lp.line_pair[pos].value)
                s=pos
            
            #YWert
            pos=lp.index_code(20,s+1,e)
            if pos:
                blocks.Entities[-1].basep.y=float(lp.line_pair[pos].value)
                s=pos
            
            #Lesen der Geometrien
            (blocks.Entities[-1].geo,warning)=self.Get_Geo(s,e,warning)
            
            #Im Debug Modus 2 mehr Infos zum Block drucken
            self.textbox.prt(("\n %s" %blocks.Entities[-1] ),2)
            
        if warning==1:
            showwarning("Import Warning","Found unsupported or only\npartly supported geometry.\nFor details see status messages!")
            
        return blocks
    #Lesen der Entities Geometrien
    def Read_Entities(self,sections):
        warning=0
        for section_nr in range(len(sections)):
            if (find(sections[section_nr-1].name,"ENTITIES") == 0):
                self.textbox.prt("\n\nReading Entities",1)
                entities=EntitiesClass(0,'Entities',[])
                (entities.geo, warning)=self.Get_Geo(sections[section_nr-1].begin+1, 
                                                    sections[section_nr-1].end-1,
                                                    warning)
    
        if warning==1:
            showwarning("Import Warning","Found unsupported or only\npartly supported geometry.\nFor details see status messages!")
            
        return entities

    #Lesen der Geometrien von Bl�cken und Entities         
    def Get_Geo(self, begin, end, warning):
        geos= []
        self.start=self.line_pairs.index_code(0,begin,end)
        old_start=self.start
        
        while self.start!=None:
            #Laden der aktuell gefundenen Geometrie
            name=self.line_pairs.line_pair[self.start].value         
            entitie_geo,warning = self.get_geo_entitie(len(geos),name, warning)

            #Hinzuf�gen der Werte Wenn es gerade gefunden wurde
            if warning==2:
                #Zur�cksetzen zu Warnung allgemein
                warning=1
            else:
                geos.append(entitie_geo)
            
            #Die n�chste Suche Starten nach dem gerade gefundenen
            self.start=self.line_pairs.index_code(0,self.start,end)            

            #Debug Informationen anzeigen falls erw�nscht                        
            if self.start==None:
                self.textbox.prt(("\nFound %s at Linepair %0.0f (Line %0.0f till %0.0f)" \
                                        %(name, old_start,old_start*2+4,end*2+4)),1)
            else:
                self.textbox.prt(("\nFound %s at Linepair %0.0f (Line %0.0f till %0.0f)" \
                                        %(name, old_start,old_start*2+4,self.start*2+4)),1)

            if len(geos)>0:
                self.textbox.prt(str(geos[-1]),2)

            old_start=self.start

        
            
        del(self.start)
        return geos, warning

    #Verteiler f�r die Geo-Instanzen
    # wird in def Get_Geo aufgerufen
    # f�r einen Release kann der ganze Code gerne wieder in einer Datei landen.
    def get_geo_entitie(self, geo_nr, name, warning):
        #Entities:
        # 3DFACE, 3DSOLID, ACAD_PROXY_ENTITY, ARC, ATTDEF, ATTRIB, BODY
        # CIRCLE, DIMENSTION, ELLIPSE, HATCH, IMAGE, INSERT, LEADER, LINE,
        # LWPOLYLINE, MLINE, MTEXT, OLEFRAME, OLE2FRAME, POINT, POLYLINE,
        # RAY, REGION, SEQEND, SHAPE, SOLID, SPLINE, XT, TOLERANCE, TRACE,
        # VERTEX, VIEWPOINT, XLINE

        # Instanz des neuen Objekts anlegen und gleichzeitig laden
        if(name=="POLYLINE"):
            geo=PolylineClass(geo_nr,self)
        elif (name=="SPLINE"):
            geo=SplineClass(geo_nr,self)
        elif (name=="ARC"):
            geo=ArcClass(geo_nr,self)
        elif (name=="CIRCLE"):
            geo=CircleClass(geo_nr,self)
        elif (name=="LINE"):
            geo=LineClass(geo_nr,self)
        elif (name=="INSERT"):
            geo=InsertClass(geo_nr,self)
        elif (name=="ELLIPSE"):
            geo=EllipseClass(geo_nr,self)
        elif (name=="LWPOLYLINE"):
            geo=LWPolylineClass(geo_nr,self)
        else:  
            self.textbox.prt(("\n!!!!WARNING Found unsupported geometry: %s !!!!" %name))
            self.start+=1 #Eins hochz�hlen sonst gibts ne dauer Schleife
            warning=2
            return [],warning
            
        return geo,warning

    #Findet die Nr. des Geometrie Layers
    def Get_Layer_Nr(self,Layer_Name):
        for i in range(len(self.layers)):
            if (find(self.layers[i].name,Layer_Name)==0):
                layer_nr=i
                return layer_nr
        layer_nr=len(self.layers)
        self.layers.append(LayerClass(layer_nr))
        self.layers[-1].name=Layer_Name
        return layer_nr
    
    #Findet die Nr. des Blocks
    def Get_Block_Nr(self,Block_Name):
        block_nr=-1
        for i in range(len(self.blocks.Entities)):
            if (find(self.blocks.Entities[i].Name,Block_Name)==0):
                block_nr=i
                break  
        return block_nr

    #Findet die beste Kontur der zusammengesetzen Geometrien
    def Get_Contour(self,entities=None):
        cont=[]

        points=self.App_Cont_or_Calc_IntPts(entities.geo,cont)
        points=self.Find_Common_Points(points)
        #points=self.Remove_Redundant_Geos(points)

        cont=self.Search_Contours(entities.geo,points,cont)
        
        return cont    
    
    #Berechnen bzw. Zuweisen der Anfangs und Endpunkte
    def App_Cont_or_Calc_IntPts(self,geo=None,cont=None):
        tol=self.config.points_tolerance.get()

        points=[]
        warning=0
        for i in range(len(geo)) :
            warning=geo[i].App_Cont_or_Calc_IntPts(cont, points, i, tol, warning)
        
    
        if warning:
            showwarning("Short Elements", ("Length of some Elements too short!"\
                                               "\nLenght must be greater then tolerance."\
                                               "\nSkipped Geometries"))
    
        return points

    #Suchen von gemeinsamen Punkten
    def Find_Common_Points(self,points=None):
        tol=self.config.points_tolerance.get()

        p_list=[]
        
        #Einen List aus allen Punkten generieren
        for p in points:
           p_list.append([p.Layer_Nr,p.be.x,p.be.y,p.point_nr,0])
           p_list.append([p.Layer_Nr,p.en.x,p.en.y,p.point_nr,1])

        #Den List sortieren        
        p_list.sort()
        #print p_list

        #Eine Schleife f�r die Anzahl der List Elemente durchlaufen
        #Start = wo die Suche der gleichen Elemente beginnen soll
        anf=[]
        
        for l_nr in range(len(p_list)):
            inter=[]
            #print ("Suche Starten f�r Geometrie Nr: %i, Punkt %i" %(p_list[l_nr][3],l_nr))
            
            if type(anf) is list:
                c_nr=0
            else:
                c_nr=anf
                
            anf=[]

            #Schleife bis n�chster X Wert Gr��er ist als selbst +tol  und Layer Gr��er gleich
            while (p_list[c_nr][0]<p_list[l_nr][0]) | \
                  (p_list[c_nr][1]<=(p_list[l_nr][1]+tol)):
                #print ("Suche Punkt %i" %(c_nr))
                

                #Erstes das �bereinstimmt is der n�chste Anfang
                if (type(anf) is list) & \
                   (p_list[c_nr][0]==p_list[l_nr][0]) & \
                   (abs(p_list[c_nr][1]-p_list[l_nr][1])<=tol):
                    anf=c_nr
                    #print ("N�chste Suche starten bei" +str(anf))
                    
                #Falls gleich anh�ngen                
                if  (p_list[c_nr][0]==p_list[l_nr][0]) &\
                    (abs(p_list[c_nr][1]-p_list[l_nr][1])<=tol) &\
                    (abs(p_list[c_nr][2]-p_list[l_nr][2])<=tol) &\
                    (c_nr!=l_nr):
                    inter.append(c_nr)
                    #print ("Gefunden" +str(inter))
                c_nr+=1

                if c_nr==len(p_list):
                    break

            #Anh�ngen der gefundenen Punkte an points
            for int_p in inter:
                #Common Anfangspunkt
                if p_list[l_nr][-1]==0:
                    points[p_list[l_nr][-2]].be_cp.append(p_list[int_p][3:5])
                #Common Endpunkt
                else:
                    points[p_list[l_nr][-2]].en_cp.append(p_list[int_p][3:5])
        return points
    
    def Remove_Redundant_Geos(self,geo=None,points=None):
        pass
#        del_points=[]
#        for p_nr in range(len(points)):
#            if not(p_nr in del_points):
#                for be_p in points[p_nr].be_cp:
#                    for en_p in points[p_nr].en_cp:
#                        if be_p[0]==en_p[0]:
#                            del_points.append(be_p[0])
#                            print ('Gleiche Punkte in Anfang: %s und Ende %s' %(be_p,en_p))
#                    
#        #L�schen der �berfl�ssigen Punkte
#        for p_nr in del_points:
#            for j in range(len(points)):
#                if p_nr==points[j].point_nr:
#                    del points[j]
#                    break
#        return points        

     #Suchen nach den besten zusammenh�ngenden Konturen
    def Search_Contours(self,geo=None,all_points=None,cont=None):
        
        points=deepcopy(all_points)
        
        while(len(points))>0:
        #for i in range(min(len(points),2)):
            #print '\n Neue Suche'
            #Wenn nichts gefunden wird dann einfach die Kontur hochz�hlen
            if (len(points[0].be_cp)==0)&( len(points[0].en_cp)==0):
                #print '\nGibt Nix'
                cont.append(ContourClass(len(cont),0,[[points[0].point_nr,0]],0))
            elif (len(points[0].be_cp)==0) & (len(points[0].en_cp)>0):
                #print '\nGibt was R�ckw�rts (Anfang in neg dir)'
                new_cont_pos=self.Search_Paths(0,[],points[0].point_nr,0,points)
                cont.append(self.Get_Best_Contour(len(cont),new_cont_pos,geo,points))
            elif (len(points[0].be_cp)>0) & (len(points[0].en_cp)==0):
                #print '\nGibt was Vorw�rt (Ende in pos dir)'
                new_cont_neg=self.Search_Paths(0,[],points[0].point_nr,1,points)
                cont.append(self.Get_Best_Contour(len(cont),new_cont_neg,geo,points))
            elif (len(points[0].be_cp)>0) & (len(points[0].en_cp)>0):                
                #print '\nGibt was in beiden Richtungen'
                #Suchen der m�glichen Pfade                
                new_cont_pos=self.Search_Paths(0,[],points[0].point_nr,1,points)
                #Bestimmen des besten Pfades und �bergabe in cont                
                cont.append(self.Get_Best_Contour(len(cont),new_cont_pos,geo,points))
                #points=self.Remove_Used_Points(cont[-1],points)

                #Falls der Pfad nicht durch den ersten Punkt geschlossen ist
                if cont[-1].closed==0:
                    #print '\nPfad nicht durch den ersten Punkt geschlossen'
                    cont[-1].reverse()
                    #print ("Neue Kontur umgedrejt %s" %cont[-1])
                    new_cont_neg=self.Search_Paths(0,[cont[-1]],points[0].point_nr,0,points)
                    cont[-1]=self.Get_Best_Contour(len(cont)-1,new_cont_neg+new_cont_pos,geo,points)
                    
            else:
                print 'FEHLER !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
        
           
            points=self.Remove_Used_Points(cont[-1],points)        
            cont[-1]=self.Contours_Points2Geo(cont[-1],all_points)
        
        return cont

    #Suchen die Wege duch die Konturn !!! REKURSIVE SCHLEIFE WAR SAU SCHWIERIG
    def Search_Paths(self,c_nr=None,c=None,p_nr=None,dir=None,points=None):

        #Richtung der Suche definieren (1= pos, 0=neg bedeutet mit dem Ende Anfangen)
            
        #Wenn es der erste Aufruf ist und eine neue Kontur angelegt werden muss         
        if len(c)==0:
            c.append(ContourClass(cont_nr=0,order=[[p_nr,dir]]))   
   
        #Suchen des Punktes innerhalb der points List (n�tig da verwendete Punkte gel�scht werden)
        for new_p_nr in range(len(points)):
                if points[new_p_nr].point_nr==p_nr:
                    break
                if new_p_nr==len(points)-1:
                    print 'WIR HABEN EIN PROBLEM'
        
        #N�chster Punkt abh�ngig von der Richtung
        if dir==0:
            weiter=points[new_p_nr].en_cp
        elif dir==1:
            weiter=points[new_p_nr].be_cp
            
        #Schleife f�r die Anzahl der Abzweig M�glichkeiten      
        for i in range(len(weiter)):
            #Wenn es die erste M�glichkeit ist Hinzuf�gen zur aktuellen Kontur
            if i==0:
                if not(c[c_nr].is_contour_closed()):
                    c[c_nr].order.append(weiter[0])
                    
            #Es gibt einen Abzweig, es wird die aktuelle Kontur kopiert und dem
            #anderen Zweig gefolgt
            elif i>0:
                if not(c[c_nr].is_contour_closed()):
                    #print 'Abzweig ist m�glich'
                    c.append(deepcopy(c[c_nr]))
                    del c[-1].order[-1]
                    c[-1].order.append(weiter[i])
                          
        for i in range(len(weiter)):
            #print 'I ist: ' +str(i)
            if i ==0:
                new_c_nr = c_nr
            else:
                new_c_nr=len(c)-len(weiter)+i
                
            new_p_nr = c[new_c_nr].order[-1][0]
            new_dir  = c[new_c_nr].order[-1][1]
            if not(c[new_c_nr].is_contour_closed()):
                c=self.Search_Paths(copy(new_c_nr),c,copy(new_p_nr),copy(new_dir),points)        
        return c 
    #Sucht die beste Kontur unter den gefunden aus (Meiner Meinung nach die Beste)
    def Get_Best_Contour(self,c_nr,c=None,geo=None,points=None):
      
        #Hinzuf�gen der neuen Kontur  
        best=None
        best_open=None
        #print ("Es wurden %0.0f Konturen gefunden" %len(c))
        for i in range(len(c)):
            #if len(c)>1:
                #print ("Kontur Nr %0.0f" %i)
                #print c[i]
                
            #Korrigieren der Kontur falls sie nicht in sich selbst geschlossen ist
            if c[i].closed==2:
                c[i].remove_other_closed_contour()
                c[i].closed=0
                c[i].calc_length(geo)
            #Suchen der besten Geometrie
            if c[i].closed==1:
                c[i].calc_length(geo)
                if best==None:
                    best=i
                else:
                    if c[best].length<c[i].length:
                        best=i
            elif c[i].closed==0:
                c[i].calc_length(geo)
                if best_open==None:
                    best_open=i
                else:
                    if c[best_open].length<c[i].length:
                        best_open=i

            #Falls keine Geschschlossene dabei ist Beste = Offene
        if best==None:
            best=best_open
                
        best_c=c[best]
        best_c.cont_nr=c_nr
        
        #print "Beste Kontur Nr:%s" %best_c

        return best_c
    
    #Alle Punkte im Pfad aus Points l�schen um n�chte Suche zu beschleunigen               
    def Remove_Used_Points(self,cont=None,points=None):
        for p_nr in cont.order:
            
            #This have to be 2 seperate loops, otherwise one element is missing
            for point in points:
                if p_nr[0]==point.point_nr:
                    del points[points.index(point)]
                    
            for point in points:
                for be_cp in point.be_cp:
                    if p_nr[0]==be_cp[0]:
                        del point.be_cp[point.be_cp.index(be_cp)]
                        break
                    
                for en_cp in point.en_cp:
                    if p_nr[0]==en_cp[0]:
                        del point.en_cp[point.en_cp.index(en_cp)]
                        break
                                  
        #R�ckgabe der Kontur       
        return points
    #Alle Punkte im Pfad aus Points l�schen um n�chte Suche zu beschleunigen               
    def Contours_Points2Geo(self,cont=None,points=None):
        #print cont.order
        for c_nr in range(len(cont.order)):
                cont.order[c_nr][0]=points[cont.order[c_nr][0]].geo_nr
        return cont
            
class dxflinepairClass:
    def __init__(self,code=None,value=None):
        self.code=code
        self.value=value
    def __str__(self):
        return '\nCode ->'+str(self.code)+'\nvalue ->'+self.value
    
class dxflinepairsClass:
    def __init__(self,line_pair=[]):
        self.nrs=0
        self.line_pair=line_pair
    def __str__(self):
        return '\nNumber of Line Pairs: '+str(self.nrs)

    #Sucht nach beiden Angaben in den Line Pairs code & value
    #optional mit start und endwert f�r die Suche
    def index_both(self,code=0,value=0,start=0,stop=-1):

        #Wenn bei stop -1 angegeben wird stop am ende der pairs        
        if stop==-1:
            stop=len(self.line_pair)
            
        #Starten der Suche innerhalb mit den angegeben parametern        
        for i in range(start,stop):
            if (self.line_pair[i].code==code) & (self.line_pair[i].value==value):
                return i
                
            
        #Wenn nicht gefunden wird None ausgeben
        return None
    
    #Sucht nach Code Angaben in den Line Pairs code & value
    #optional mit start und endwert f�r die Suche
    def index_code(self,code=0,start=0,stop=-1):

        #Wenn bei stop -1 angegeben wird stop am ende der pairs        
        if stop==-1:
            stop=len(self.line_pair)
            
        #Starten der Suche innerhalb mit den angegeben parametern        
        for i in range(start,stop):
            if (self.line_pair[i].code==code):
                return i
            
        #Wenn nicht gefunden wird None ausgeben
        return None
            
class LayerClass:
    def __init__(self,Nr=0, name=''):
        self.Nr= Nr
        self.name = name
    def __str__(self):
        # how to print the object
        return '\nNr ->'+str(self.Nr)+'\nName ->'+self.name
    def __len__(self):
        return self.__len__

class SectionClass:
    def __init__(self,Nr=0, name='',begin=0,end=1):
        self.Nr= Nr
        self.name = name
        self.begin= begin
        self.end = end  
    def __str__(self):
        # how to print the object
        return '\nNr ->'+str(self.Nr)+'\nName ->'+self.name+'\nBegin ->'+str(self.begin)+'\nEnd: ->'+str(self.end)
    def __len__(self):
        return self.__len__

class EntitiesClass:
    def __init__(self,Nr=0, Name='',geo=[],cont=[]):
        self.Nr= Nr
        self.Name = Name
        self.basep = PointClass(x=0.0,y=0.0)
        self.geo=geo
        self.cont=cont
        
    def __str__(self):
        # how to print the object
        return '\nNr:      %s' %(self.Nr) +\
                '\nName:    %s' %(self.Name)+\
                '\nBasep:   %s' %(self.basep)+\
                '\nNumber or Geometries: %i' %(len(self.geo))+\
                '\nNumber of Contours:   %i'  %(len(self.cont))
                
               
    def __len__(self):
        return self.__len__
    
    #Gibt einen List mit den Benutzten Layers des Blocks oder Entities zur�ck
    def get_used_layers(self):
        used_layers=[]
        for i in range(len(self.geo)):
            if (self.geo[i].Layer_Nr in used_layers)==0:
                used_layers.append(self.geo[i].Layer_Nr)
        return used_layers
      #Gibt die Anzahl der Inserts in den Entities zur�ck
    def get_insert_nr(self):
        insert_nr=0
        for i in range(len(self.geo)):
            if ("Insert" in self.geo[i].Typ):
                insert_nr+=1
        return insert_nr
    
class BlocksClass:
    def __init__(self,Entities=[]):
        self.Entities=Entities
    def __str__(self):
        # how to print the object
        s= '\nBlocks:\nNumber of Blocks ->'+str(len(self.Entities))
        for entitie in self.ties:
            s=s+str(entitie)
        return s
