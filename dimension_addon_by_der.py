'''
jan.holinka@seznam.cz
Created by Jan Holinka
This file is part of Dimensions and Lines. Dimensions and Lines is free software; you can redistribute it 
and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; 
either version 3 of the License, or (at your option) any later version. This program is distributed in the hope 
that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or 
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details. You should have received 
a copy of the GNU General Public License along with this program; if not, see <https://www.gnu.org/licenses>.
'''

#version: 1.0.8

from . import cameras_setup
from . import hatches_operator
from . import lines_operators
from . import dim_two_vert_op
from . import dim_realtime_op
from . import dim_remake_op
import bpy # type: ignore
import math # type: ignore
import mathutils # type: ignore
import gpu # type: ignore
import blf # type: ignore
from timeit import default_timer as timer
from gpu_extras.batch import batch_for_shader # type: ignore

class VIEW3D_PT_dimensions(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Dimensions and Lines"
    bl_label = "Dimensions"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        col = layout.column(align=True)
        col.scale_y = 1.5
        propsTe = col.operator('mesh.dimension_two_vert', text = 'Dimension from 2 vertices')
        propsTe.boolFromModal = False
        propsTe.boolFirstRun = True

        col.operator('mesh.realtime_dimension', text = 'Realtime(mouse) dimensions')

        col = layout.column(align=True)
        col.operator('mesh.remake_dimension', text = 'Remake dimension(load settings)')

        col = layout.column(align=True)
        col.use_property_split = False
        col.prop(context.scene.DIMENSION, "ignoreUndo", text = "Rewrite Redo panel changes")
        
        col.separator(factor=2.0) #space

        col = layout.column(align=True)
        col.prop(context.scene.DIMENSION, "scale", text = "Scale 1:")

        col = layout.column(align=True)
        col.prop(context.scene.DIMENSION, "dpi", text = "DPI:")

        row = layout.row()
        row.prop(context.scene.DIMENSION, "paperFormats", text = "Paper:")
        row.prop(context.scene.DIMENSION, "widePaper", text = "Wide")

        row = layout.row()
        row.prop(context.scene.DIMENSION, "jednotky", text = "Units:")
        row.prop(context.scene.DIMENSION, "showUnits", text = "Show")
        
        row = layout.row()
        row.prop(context.scene.DIMENSION, "decPlaces", text = "Dec. places:")

        col = layout.column(align=True)
        col.prop(context.scene.DIMENSION, "fontsArray", text = "Font:")

        col = layout.column(align=True)
        col.operator("font.open", text= "Load Font")

        col = layout.column(align=True)
        col.label(text = "Dimension type:")
        col.prop(context.scene.DIMENSION, "dimType", text = "")

        col = layout.column(align=True)
        col.label(text = "Camera object:  " + context.scene.DIMENSION.cameraOb, icon= 'VIEW_CAMERA')
        col.operator("camera.dimselect", text= "Set selected object as camera")

        col = layout.column(align=True)
        col.scale_y = 1.8
        col.operator("camera.dimsetupcam", text= "Set camera and resolution")

        col.separator(factor=0.7) #space

        col = self.layout.column(align=True)
        col.scale_y = 1.5
        col.label(text = "Lines:", icon= 'IPO_CONSTANT')
        col.operator('mesh.lines', text = 'Add thickness to edges').boolFirstRun = True

        col = self.layout.column(align=True)
        col.operator('mesh.lines_clear', text = 'Clear thickness')

        col = layout.column(align=True)
        col.prop(context.scene.DIMENSION, "lineTypes", text = "Type:")

        col = layout.column(align=True)
        col.prop(context.scene.DIMENSION, "lineWidths", text = "Width:")

        col.separator(factor=1.0) #space

        col = layout.column(align=True)
        col.scale_y = 1.5
        col.label(text = "Hatches:", icon= 'OUTLINER_DATA_LIGHTPROBE')
        col.operator('mesh.hatches', text = 'Create hatch from selected closed area').boolFirstRun = True

        col = layout.column(align=True)
        col.prop(context.scene.DIMENSION, "hatchesTypes", text = "Hatch type:") 


        #DPI and paper format - camera set - size of dimensions set
        #2,54cm - 300 pixel (300DPI), A4 - 297x210 = 297/25.4 * 300 = 3 507.874
        #                                           210/25.4 * 300 = 2 480.315
        #A4 wide
        #1:100 297mm =      = 29.7m - fits on A4 on wide - ortho_scale = 29.7
        #1:50  297mm =      = 14.85m - fits on A4 on wide - ortho_scale = 29.7/2 - 14.85
        #1:10  297mm =      = 2.97 m - fits on A4 on wide - ortho_scale = 2.97
        #A3 wide
        #420x297 = 420/25.4 * 300 = 4 960.63
        #1:100 420mm = 42m - fits on A3 on wide - ortho scale 42.0 - setup for bigger paper size
        #______________________________________________________________________________________________________________________________
        #line width - normal, fat, very fat 1:2:4
        #0.13, 0.18, 0.25, 0.35, 0.5, 0.7, 1.0, 1.4, 2.0 mm
        #0.25 - 0.5 - 1.0
        #normal - fat - very fat

        #2mm are 300 dpi, 0.2/25.4 * 300 = 2.362px
        #for 1:100 is then width in Blender units 2mm * 100 = 200mm = 20cm = 2dm = 0.2m atc. 
        #for 1:10 is then width in Blender units 2mm * 10 = 20mm = 2cm = 0.2dm = 0.02m atc.


    
    def invoke(self, context, event):

        shortR = context.space_data.region_3d.view_rotation
        if shortR[0] == 1.0 and shortR[1] == 0.0 and shortR[2] == 0.0 and shortR[3] == 0.0:
            self.lockAxisZ = True
        if shortR[0] == 0.0 and shortR[1] == 1.0 and shortR[2] == 0.0 and shortR[3] == 0.0:
            self.lockAxisZ = True

        if shortR[0] == 0.7071067690849304 and shortR[1] == 0.7071067690849304 and shortR[2] == 0.0 and shortR[3] == 0.0:
            self.report({'ERROR'}, "Dimensions are by default aligned to X-Y plane - invisible from sides - please use Top view, or any other arbitrary angle.")
            return {'FINISHED'}
        if shortR[0] == 0.0 and shortR[1] == 0.0 and shortR[2] == 0.7071068286895752 and shortR[3] == 0.7071068286895752:
            self.report({'ERROR'}, "Dimensions are by default aligned to X-Y plane - invisible from sides - please use Top view, or any other arbitrary angle.")
            return {'FINISHED'}
        if shortR[0] == 0.5 and shortR[1] == 0.5 and shortR[2] == 0.5 and shortR[3] == 0.5:
            self.report({'ERROR'}, "Dimensions are by default aligned to X-Y plane - invisible from sides - please use Top view, or any other arbitrary angle.")
            return {'FINISHED'}
        if shortR[0] == 0.5 and shortR[1] == 0.5 and shortR[2] == -0.5 and shortR[3] == -0.5:
            self.report({'ERROR'}, "Dimensions are by default aligned to X-Y plane - invisible from sides - please use Top view, or any other arbitrary angle.")
            return {'FINISHED'}

        #pokud view rotation jeden z pripadu, tak lockneme axis nejak...

        if bpy.context.mode == 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        self.snapFinished = False

        args = (context,)
        self.nevimHandle = bpy.types.SpaceView3D.draw_handler_add(self.drawingSnap, args, 'WINDOW', 'POST_PIXEL')
        self.nevimHandle2 = bpy.types.SpaceView3D.draw_handler_add(self.drawingAxis, args, 'WINDOW', 'POST_VIEW')

        context.window_manager.modal_handler_add(self)

        self.edgesMiddleText = 'active'
        if context.scene.DIMENSION.ignoreMid == True:
            self.edgesMiddleText = 'turned off'
        if self.continueMode == False:
            continueModeText = 'turned off'
        self.textToDraw = 'select first point of dimension | snaping to edges middle is ' + self.edgesMiddleText + ' - switch with M | continue mode is ' + self.continueModeText + ' - switch with C'

        return {'RUNNING_MODAL'}

    def drawingSnap (self, context):
        point = self.snap2Dfin
        sB = 12
        indiciesLines = ((4,6),(5,7))
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        if self.osazeno == True:
            sB = 7
            indiciesLines = ((0,2),(2,3),(3,1),(1,0))
            if self.middlePointHelp == True:
                indiciesLines = ((2,3),(3,4),(4,2))
        coords =((point[0] - sB,point[1] + sB),(point[0]+ sB,point[1] + sB),(point[0]-sB,point[1]-sB),(point[0]+sB,point[1] -sB),(point[0],point[1] +sB),(point[0]-sB,point[1]),(point[0],point[1]-sB),(point[0]+sB,point[1]))
        batch2 = batch_for_shader(shader, 'LINES', {"pos": coords},indices=indiciesLines)
        shader.uniform_float("color", (0.921, 0.8117, 0.204, 1))
        batch2.draw(shader)

        font_id = 0  #, need to find out how best to get this.
        # draw some text
        blf.position(font_id, 15, 15, 0)
        blf.size(font_id, 10.0)
        blf.color(font_id, 1.0, 1.0, 1.0, 1.0)
        blf.draw(font_id, self.textToDraw)
        blf.position(font_id, 15, 30, 0)
        lockedAxis = ''
        if self.lockAxisX == True:
            lockedAxis = lockedAxis + ' X'
        if self.lockAxisY == True:
            lockedAxis = lockedAxis + ' Y'
        if self.lockAxisZ == True:
            lockedAxis = lockedAxis + ' Z'
        blf.draw(font_id, 'locked axis:' + lockedAxis)
        blf.position(font_id, 15, 45, 0)
        blf.draw(font_id, 'length: ' + self.delkaManual)

        if self.snapFinished == False:
            blf.position(font_id, 15, 60, 0)
            blf.size(font_id, 8.0)
            blf.draw(font_id, 'snaping loading - objects loaded: ' + str(self.snapObjectsIterator) + ' , current vert: ' + str(self.snapVerticeIterator) + ' , current middle: ' + str(self.snapMiddlesIterator))

    def drawingAxis (self, context):
        point = self.prvniBodKotyCoord
        infiniteLenght = 1000
        if self.lockAxisX == True:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
            indiciesLines = ((0,1),)
            shader.uniform_float("color", (0.95, 0.40, 0.40, 1))
            coords =((point[0] - infiniteLenght,point[1],point[2]),(point[0] + infiniteLenght,point[1],point[2]))
            batch = batch_for_shader(shader, 'LINES', {"pos": coords},indices=indiciesLines)
            batch.draw(shader)
        if self.lockAxisY == True:
            shader2 = gpu.shader.from_builtin('UNIFORM_COLOR')
            indiciesLines2 = ((0,1),)
            shader2.uniform_float("color", (0.40, 0.95, 0.40, 0.4))
            coords2 =((point[0],point[1] - infiniteLenght,point[2]),(point[0],point[1] + infiniteLenght,point[2]))
            batch2 = batch_for_shader(shader2, 'LINES', {"pos": coords2},indices=indiciesLines2)
            batch2.draw(shader2)
        if self.lockAxisZ == True:
            shader3 = gpu.shader.from_builtin('UNIFORM_COLOR')
            indiciesLines3 = ((0,1),)
            shader3.uniform_float("color", (0.40, 0.40, 0.95, 0.4))
            coords3 =((point[0],point[1],point[2]- infiniteLenght),(point[0],point[1],point[2]+ infiniteLenght))
            batch3 = batch_for_shader(shader3, 'LINES', {"pos": coords3},indices=indiciesLines3)
            batch3.draw(shader3)

    def setupPropsByUI(self,context):
        #DPI a papir daji dohromady rozliseni - resime jenom vetsi rozmer A5-210 A4-297 A3-420 A2-594 A1-841 A0-1189
        self.otocit = False
        self.tloustka = 0.00028*context.scene.DIMENSION.scale
        self.protazeni = 0.0012*context.scene.DIMENSION.scale
        self.odsazeniHlavni = 0.006*context.scene.DIMENSION.scale
        self.odsazeniZakladna = 0.002*context.scene.DIMENSION.scale
        self.presahKolmice = 0.0012*context.scene.DIMENSION.scale
        self.meritko = context.scene.DIMENSION.scale
        self.delkaSikmeCar = 0.0024*context.scene.DIMENSION.scale
        self.textSize = 0.0036*context.scene.DIMENSION.scale
        self.rotace = 0
        self.textRotace = 0
        if context.scene.DIMENSION.jednotky == 'mm':
            self.distanceScale = 1000
        if context.scene.DIMENSION.jednotky == 'cm':
            self.distanceScale = 100
        if context.scene.DIMENSION.jednotky == 'dm':
            self.distanceScale = 10
        if context.scene.DIMENSION.jednotky == 'm' or context.scene.DIMENSION.jednotky == 'None':
            self.distanceScale = 1
        if context.scene.DIMENSION.jednotky == 'km':
            self.distanceScale = 0.001
        if context.scene.DIMENSION.jednotky == 'ft in':
            self.distanceScale = 1
        if context.scene.DIMENSION.jednotky == 'inches':
            self.distanceScale = 1
        self.pocetDesetMist = context.scene.DIMENSION.decPlaces
        #distanceScale

    def setupUnitsScale(self,context):
        if context.scene.DIMENSION.jednotky == 'mm':
            self.distanceScale = 1000
            #self.pocetDesetMist = 0
        if context.scene.DIMENSION.jednotky == 'cm':
            self.distanceScale = 100
            #self.pocetDesetMist = 2
        if context.scene.DIMENSION.jednotky == 'dm':
            self.distanceScale = 10
            #self.pocetDesetMist = 1
        if context.scene.DIMENSION.jednotky == 'm' or context.scene.DIMENSION.jednotky == 'None':
            self.distanceScale = 1
            #self.pocetDesetMist = 3
        if context.scene.DIMENSION.jednotky == 'km':
            self.distanceScale = 0.001
            #self.pocetDesetMist = 4
        if context.scene.DIMENSION.jednotky == 'ft in':
            self.distanceScale = 1
            #self.pocetDesetMist = 0
        if context.scene.DIMENSION.jednotky == 'inches':
            self.distanceScale = 1

    def globalsSave(self):
        context = bpy.context
        context.scene.DIMENSION.protazeniG = self.protazeni
        context.scene.DIMENSION.odsazeniHlavniG = self.odsazeniHlavni
        context.scene.DIMENSION.odsazeniZakladnaG = self.odsazeniZakladna
        context.scene.DIMENSION.presahKolmiceG = self.presahKolmice
        context.scene.DIMENSION.otocitG = self.otocit
        context.scene.DIMENSION.pocetDesetMistG = self.pocetDesetMist
        context.scene.DIMENSION.textOffsetG = self.textOffset
        context.scene.DIMENSION.textOffsetHorG = self.textOffsetHor
        context.scene.DIMENSION.rotaceG = self.rotace
        context.scene.DIMENSION.tloustkaG = self.tloustka
        context.scene.DIMENSION.delkaSikmeCarG = self.delkaSikmeCar
        context.scene.DIMENSION.rotaceTextuG = self.textRotace
        context.scene.DIMENSION.textSizeG = self.textSize
        context.scene.DIMENSION.distanceScaleG = self.distanceScale

    def globalsLoad(self):
        context = bpy.context
        self.protazeni = context.scene.DIMENSION.protazeniG
        self.odsazeniHlavni = context.scene.DIMENSION.odsazeniHlavniG
        self.odsazeniZakladna = context.scene.DIMENSION.odsazeniZakladnaG
        self.presahKolmice = context.scene.DIMENSION.presahKolmiceG
        self.otocit = context.scene.DIMENSION.otocitG
        self.pocetDesetMist = context.scene.DIMENSION.pocetDesetMistG
        self.textOffset = context.scene.DIMENSION.textOffsetG
        self.textOffsetHor = context.scene.DIMENSION.textOffsetHorG
        self.meritko = context.scene.DIMENSION.meritkoG
        self.rotace = context.scene.DIMENSION.rotaceG
        self.textRotace = context.scene.DIMENSION.rotaceTextuG
        self.tloustka = context.scene.DIMENSION.tloustkaG
        self.delkaSikmeCar = context.scene.DIMENSION.delkaSikmeCarG
        self.textSize = context.scene.DIMENSION.textSizeG
        self.distanceScale = context.scene.DIMENSION.distanceScaleG
        self.posunKolecka = context.scene.DIMENSION.odsazeniZakladnaG

    def makeImperial(self, context, KotaNumber) -> str:
        #nejdriv cele cislo pro foot a float pro inch
        foot = 0
        foot = int(KotaNumber//0.3048)
        inch = 0.0
        inch = (KotaNumber - (foot * 0.3048)) / 0.0254
        if math.isclose(inch,12,abs_tol = 0.00001) == True:
            foot = foot + 1
            inch = 0.0
        textInch = ''
        textInch = str(round(inch, self.pocetDesetMist))
        textInch = self.zaokrouhlNa(textInch, self.pocetDesetMist)
        vysledek = ''
        if context.scene.DIMENSION.showUnits == True:
            vysledek = str(foot) + 'ft ' + textInch + 'in'
        else:
            vysledek = str(foot) + '\' ' + textInch + '\"'
        return vysledek
    
    def makeInches(self, context, KotaNumber) -> str:
        #nejdriv cele cislo pro foot a float pro inch
        inch = 0.0
        inch = KotaNumber / 0.0254
        #if math.isclose(inch,12,abs_tol = 0.00001) == True:
            #inch = 0.0
        textInch = ''
        textInch = str(round(inch, self.pocetDesetMist))
        textInch = self.zaokrouhlNa(textInch, self.pocetDesetMist)
        vysledek = ''
        if context.scene.DIMENSION.showUnits == True:
            vysledek = textInch + ' in'
        else:
            vysledek = textInch + '\"'
        return vysledek
    
    def vratBodMeziDvemaBody(self, bod1: list[float], bod2: list[float]) -> mathutils.Vector:
        vysledek = mathutils.Vector((0.0, 0.0, 0.0))
        vysledek[0] = (bod1[0] + bod2[0])/2
        vysledek[1] = (bod1[1] + bod2[1])/2
        vysledek[2] = (bod1[2] + bod2[2])/2
        return vysledek
    
    def smerovyVektor(self, vektorBase: list[float], vektorSmer: list[float]) -> list[float]:
        sX = vektorSmer[0] - vektorBase[0]
        sY = vektorSmer[1] - vektorBase[1]
        sZ = vektorSmer[2] - vektorBase[2]
        vysledek = [sX, sY, sZ]
        return vysledek
    
    def planeNormalZflatLined(self, vektorBase: list[float], vektorSmer: list[float]) -> list[float]:
        sX = vektorSmer[0] - vektorBase[0]
        sY = vektorSmer[1] - vektorBase[1]
        sZ = vektorSmer[2] - vektorBase[2]

        #tohle resi kdyz mame plane na svislo
        if sX == 0 and sY == 0:
            sZ = 0
            sX2 = 1
            if self.otocit == True:
                sX2 = -1
            sY2 = 0
        else:
            sZ = 0
            sX2 = sY
            sY2 = -sX

        vysledek = [sX2, sY2, sZ]
        return vysledek
    
    #vzalenost uz je spocitana na nejvetsi abs osu, odsadi jakoze kolmo v ose osaRoviny na vektorSmerOrig od vektorBase
    def odsad (self, vektorBase: list[float], vektorSmerOrig: list[float], osaRoviny: int, vzdalenost: float) -> list[float]:
        #vektor opacnej vektorSmer, ale tak, ale osaRoviny - nejdriv [2] tedy z bezezmen
        #vlastne jakoby muzu vytvorit 2D rovinu ne? 

        #otocim vektor - uz je treba dle osaRoviny do spravne osy - zatim nevyuzite
        vektorSmer = [0.0,0.0,0.0]
        if osaRoviny == 2: #tzn ze je to pudorys ze zhora - Zosa je nulova
            vektorSmer[0] = vektorSmerOrig[1]#podle toho na ktery dam minus, tak na tu stranu se vektor/kota otoci
            vektorSmer[1] = -vektorSmerOrig[0]
        
        #pokud je uplna svislice, tak vektor smer vytahujeme do osy x [0], pac je to prvni pohled na num pod 1
        if vektorSmerOrig[0] == 0 and vektorSmerOrig[1] == 0:
            vektorSmer[0] = vektorSmerOrig[2]    
            #vektorSmer[0] = vektorSmer[0] * math.cos(self.rotace/(180/math.pi))
            #vektorSmer[1] = vektorSmer[0] * math.sin(self.rotace/(180/math.pi))
        #print('vektorSmer')
        #print(vektorSmer)

        rozhodovac = 0 #nejvetsi je x [0]
        if abs(vektorSmer[1]) > abs(vektorSmer[0]):
            rozhodovac = 1
        if abs(vektorSmer[2]) > abs(vektorSmer[1]) and rozhodovac == 1:
            rozhodovac = 2
        if abs(vektorSmer[2]) > abs(vektorSmer[0]) and rozhodovac == 0:
            rozhodovac = 2

        #prepocitame vzdalenost na novy vektor
        vzdalenost = self.vzdalenostNejOsa(vektorSmer, vzdalenost)
        #print('vzdalenost')
        #print(vzdalenost)

        sourX = vektorBase[0]
        sourY = vektorBase[1]
        sourZ = vektorBase[2]

        if rozhodovac == 0:
            sourX = vzdalenost + vektorBase[0]
            if vektorSmer[0] == 0:
                sourY = (0) * vzdalenost + vektorBase[1] 
            else:
                sourY = (vektorSmer[1] / vektorSmer[0]) * vzdalenost + vektorBase[1]
            sourZ = sourZ #na Z nesaham?
            vysledek = [sourX, sourY, sourZ]

        if rozhodovac == 1:
            sourX = (vektorSmer[0] / vektorSmer[1]) * vzdalenost + vektorBase[0]
            # print(vektorSmer[0], vektorSmer[1], vzdalenost, vektorBase[0])
            sourY = vzdalenost + vektorBase[1]
            sourZ = sourZ #na Z nesaham?
            vysledek = [sourX, sourY, sourZ]

        vysledek = [sourX, sourY, sourZ]

        #print('vysledek')
        #print(vysledek)

        return vysledek
    
    def pripoctiNejOsa(self, vektorBase: list[float], vektorSmer: list[float], vzdalenost: float) -> list[float]:

        vzdalenost = self.vzdalenostNejOsa(vektorSmer, vzdalenost)

        #zjistim ktery je vetsi - mozna potom
        rozhodovac = 0 #nejvetsi je x [0]
        if abs(vektorSmer[1]) > abs(vektorSmer[0]):
            rozhodovac = 1
        if abs(vektorSmer[2]) > abs(vektorSmer[1]) and rozhodovac == 1:
            rozhodovac = 2
        if abs(vektorSmer[2]) > abs(vektorSmer[0]) and rozhodovac == 0:
            rozhodovac = 2
        #print ('z ', vektorSmer[0], vektorSmer[1], vektorSmer[2], 'je nejvesti', rozhodovac)

        #pripad pro z [0]
        if rozhodovac == 0:
            sX = vzdalenost + vektorBase[0]
            sY = (vektorSmer[1] / vektorSmer[0]) * vzdalenost + vektorBase[1]
            sZ = (vektorSmer[2] / vektorSmer[0]) * vzdalenost + vektorBase[2]
            vysledek = [sX, sY, sZ]

        #pripad pro z [1]
        if rozhodovac == 1:
            sX = (vektorSmer[0] / vektorSmer[1]) * vzdalenost + vektorBase[0]
            sY = vzdalenost + vektorBase[1]
            sZ = (vektorSmer[2] / vektorSmer[1]) * vzdalenost + vektorBase[2]
            vysledek = [sX, sY, sZ]

        #pripad pro z [2]
        if rozhodovac == 2:
            sX = (vektorSmer[0] / vektorSmer[2]) * vzdalenost + vektorBase[0]
            sY = (vektorSmer[1] / vektorSmer[2]) * vzdalenost + vektorBase[1]
            sZ = vzdalenost + vektorBase[2]
            vysledek = [sX, sY, sZ]
        
        return vysledek

    # podle nejvetsiho vektoru v absolutni hodnote dopocita pripocet k dane ose/vektoru
    def vzdalenostNejOsa(self, vektorSmer: list[float], vzdalenost: float) -> float:
        #zjistime nejvetsi osu v abs hodnote
        biggestAbs = vektorSmer[0]
        if abs(vektorSmer[1]) > abs(biggestAbs):
            biggestAbs = vektorSmer[1]
        if abs(vektorSmer[2]) > abs(biggestAbs):
            biggestAbs = vektorSmer[2]
        uhlopricka = (vektorSmer[0] * vektorSmer[0]) + (vektorSmer[1] * vektorSmer[1]) + (vektorSmer[2] * vektorSmer[2])
        #print('VZDAL')
        #print(vektorSmer[0])
        #print(vektorSmer[1])
        #print(vektorSmer[2])
        uhlopricka = math.sqrt(uhlopricka)
        if uhlopricka == 0:
            vysledek = 0
        else:
            vysledek = vzdalenost/uhlopricka

        return biggestAbs * vysledek

    def vzdalenostMeziDvemaBody(self, bod1: list[float], bod2: list[float]) -> float:
        del1 = bod1[0] - bod2[0]
        del2 = bod1[1] - bod2[1]
        del3 = bod1[2] - bod2[2]
        vysledekSq = (del1*del1) + (del2*del2) + (del3*del3)
        vysledek = math.sqrt(vysledekSq)

        return vysledek

    def zaokrouhlNa(self, text: str, pocet: int) -> str:
        counter = 0
        boolZaTeckou = False
        vysledek = ''
        for i in text:
            if i == '.':
                if pocet == 0:
                    return vysledek
                boolZaTeckou = True
            if boolZaTeckou == True:  
                if counter == pocet + 1:
                    return vysledek
                counter += 1
            vysledek = vysledek + i
        if counter < pocet + 1:
            for i in range(pocet + 1 - counter):
                vysledek = vysledek + '0'
        return vysledek
    
    def vymenTeckuZaCarku(self, text: str) -> str:
        vysledek = ''
        for i in text:
            if i == '.':
                vysledek = vysledek + ','
            else:
                vysledek = vysledek + i
        return vysledek

    def rotaceDvaBody(self, obj, point1, point2):
        sX = point2[0] - point1[0]
        sY = point2[1] - point1[1]
        sZ = point2[2] - point1[2]
        vektorSmer = [sX, sY, sZ]
        
        #NASLEDUJICI KOD OTOCI OBJEKT PODLE VEKTORU CISTE PODLE SVISLE OSY - JAKO KDYZ SE HLAVOU OTOCIM DO SPRAVNE SMERU A NERESIM ZATIM VYSKU 
        #IF JSOU SWITCHE K POKRYTI 360 (PAC ATAN FUNGUJE JENOM DO 180)
        if vektorSmer[0] == 0 and vektorSmer[2] >= 0:
            obj.rotation_euler[2] = math.pi/2 
        elif vektorSmer[0] == 0 and vektorSmer[2] < 0:
            obj.rotation_euler[2] = -math.pi/2 
        else:
            obj.rotation_euler[2] = math.atan(vektorSmer[1]/vektorSmer[0])

        #prictu PI dle orientace
        if vektorSmer[0] > 0: #tohle jednoduse otaci na druhou stranu jakoby - ty uhle vsechny fungujou v ramci 180 a ja mam 360 - to proste doresuju rucne - nize to same
            obj.rotation_euler[2] = obj.rotation_euler[2] + (math.pi) 

        if vektorSmer[0] == 0:
            if vektorSmer[1] == 0:
                obj.rotation_euler[2] = obj.rotation_euler[2] + (math.pi) 
            if vektorSmer[1] > 0:
                if vektorSmer[2] >= 0:
                    obj.rotation_euler[2] = obj.rotation_euler[2] + (math.pi) 
            if vektorSmer[1] < 0:
                if vektorSmer[2] < 0:
                    obj.rotation_euler[2] = obj.rotation_euler[2] + (math.pi) 

        #NO A TADY JENOM NATOCIM OSU Y PODLE ATAN - JAKO KDYZ SE TED DIVAM NAHORU DOLU V NATOCENEM SMERU A POTREBUJI PRIHLEHLOU STRANU TROJUHLENIKA, 
        #COZ JE USECKA Z MEHO OKA NA BOD V PROSTORU - DOPOCITAVAM PYTHAGOREM
        protilehla = vektorSmer[2] 
        #prilehla je z = 0 a odmocnina z a2 + b2, a2 je rozdil v x a b2 v y
        prilehla = math.sqrt(((point1[0] - point2[0])*(point1[0] - point2[0])) + ((point1[1] - point2[1])*(point1[1] - point2[1])))
        if prilehla == 0:
            obj.rotation_euler[1] = math.pi/2
        else:
            obj.rotation_euler[1] = math.atan(protilehla/prilehla)

    def pripoctiX(self, vektorBase: list[float], vzdalenost: float) -> list[float]:
        posunutyBod = [vektorBase[0] + vzdalenost,vektorBase[1],vektorBase[2]]
        return posunutyBod
    
    def pripoctiY(self, vektorBase: list[float], vzdalenost: float) -> list[float]:
        posunutyBod = [vektorBase[0],vektorBase[1] + vzdalenost,vektorBase[2]]
        return posunutyBod  

class DIMENSION_GLOBALS(bpy.types.PropertyGroup):
    def get_fonts(self,context):
        fontsArray = []
        fontyE = True
        for font in bpy.data.fonts:
            toAppend = (font.name, font.name, "Font type")
            fontsArray.append(toAppend)
            fontyE = False
        if fontyE == True:
            toAppend = ('Bfont Regular', 'Bfont Regular', "Font type")
            fontsArray.append(toAppend)
        return fontsArray

    paperFormatsTmp = (('A5','A5','Paper format'),('A4','A4','Paper format'),('A3','A3','Paper format'),('A2','A2','Paper format'), ('A1','A1','Paper format'), ('A0','A0','Paper format'), ('Letter','Letter','Paper format'),
                       ('Legal','Legal','Paper format'), ('Ledger','Ledger','Paper format'), ('ARCH A','ARCH A','Paper format'), ('ARCH B','ARCH B','Paper format'), ('ARCH C','ARCH C','Paper format'), ('ARCH D','ARCH D','Paper format'), ('ARCH E','ARCH E','Paper format'),
                       ('ANSI A','ANSI A','Paper format'), ('ANSI B','ANSI B','Paper format'), ('ANSI C','ANSI C','Paper format'), ('ANSI D','ANSI D','Paper format'), ('ANSI E','ANSI E','Paper format'))
    unitsArray = (('None','None','Units'), ('km','km','Units'),('m','m','Units'),('dm','dm','Units'),('cm','cm','Units'), ('mm','mm','Units'), ('ft in', 'ft in', 'Units'), ('inches', 'inches', 'Units'))
    dimTypeArray = (('Slope','Slope','Dimension type'),('Slope no overlap','Slope no overlap','Dimension type'), ('Arrow in','Arrow in','Dimension type'),('Arrow out','Arrow out','Dimension type'),('Arrow open','Arrow open','Dimension type'))
    lineTypesArray = (('Straight','Straight','Line type'),('Dashed','Dashed','Line type'), ('Dotted','Dotted','Line type'),('Dash-dotted','Dash-dotted','Line type'))
    lineWidthsArray = (('Thin','Thin','Line width'),('Normal','Normal','Line width'), ('Thick','Thick','Line width'),('Very Thick','Very Thick','Line width'))
    hatchesArray = (('Lines','Lines','Straight lines'),('Grid','Grid','Grid'),('Lines dashed','Lines dashed','Dashed lines'),('Dots','Dots','Dots'), ('3-1 Lines','3-1 Lines','3-1 Lines'))

    protazeniG: bpy.props.FloatProperty( name = 'protazeniG', default= 1,) #type: ignore
    odsazeniHlavniG: bpy.props.FloatProperty( name = 'odsazeniHlavniG', default= 1.4,) #type: ignore
    odsazeniZakladnaG: bpy.props.FloatProperty( name = 'odsazeniZakladnaG', default= 0.4,) #type: ignore
    presahKolmiceG: bpy.props.FloatProperty( name = 'presahKolmiceG', default= 0.6,) #type: ignore
    otocitG: bpy.props.BoolProperty( name = 'otocitG', default= False,) #type: ignore
    pocetDesetMistG: bpy.props.IntProperty( name = 'pocetDesetMistG', default= 3,) #type: ignore
    textOffsetG: bpy.props.FloatProperty( name = 'textOffsetG', default= 0,) #type: ignore
    textOffsetHorG: bpy.props.FloatProperty( name = 'textOffsetHorG', default= 0,) #type: ignore
    meritkoG: bpy.props.IntProperty( name = 'meritkoG', default= 1,) #type: ignore
    rotaceG: bpy.props.IntProperty( name = 'rotaceG', default= 0,) #type: ignore
    rotaceTextuG: bpy.props.IntProperty( name = 'rotaceTextuG', default= 0,) #type: ignore
    tloustkaG: bpy.props.FloatProperty( name = 'tloustkaG', default= 0.1,) #type: ignore
    delkaSikmeCarG: bpy.props.FloatProperty( name = 'delkaSikmeCarG', default= 1,) #type: ignore
    textSizeG: bpy.props.FloatProperty(name="textSizeG",description="text size",default=1,min=0,) #type: ignore
    distanceScaleG: bpy.props.FloatProperty(name="distanceScaleG",description="scale for distance calculation",default = 1,min = 0,step=1, precision= 3) #type: ignore
    lastUsedHatchG: bpy.props.StringProperty(name = 'lastUsedHatch', default = "", ) #type: ignore

    fontAdres: bpy.props.StringProperty(name = 'Font', default='//',subtype = 'DIR_PATH',) #type: ignore
    fontsArray: bpy.props.EnumProperty(items = get_fonts, description= "Select font") #type: ignore
    #blender item - description, indetifier, name
    dpi: bpy.props.IntProperty(name = "dpi", default = 300, min = 72, max = 600,) #type: ignore
    paperFormats: bpy.props.EnumProperty(items = paperFormatsTmp, description= "Paper format") #type: ignore
    widePaper: bpy.props.BoolProperty(name="widePaper",default = True) #type: ignore
    scale: bpy.props.IntProperty(name = "scale", default = 100, min = 1, max = 10000) #type: ignore
    jednotky: bpy.props.EnumProperty(items = unitsArray, description= "Units") #type: ignore
    decPlaces: bpy.props.IntProperty(name = "decPlaces", default = 3, min = 0, max = 8, description = "Decimal places") #type: ignore
    cameraOb: bpy.props.StringProperty(name = 'cameraObject', default = "None", ) #type: ignore
    dimType: bpy.props.EnumProperty(items = dimTypeArray, description= "Dimension types") #type: ignore
    ignoreUndo: bpy.props.BoolProperty(name="ignoreUndo",default = True) #type: ignore
    showUnits: bpy.props.BoolProperty(name="showUnits",default = True) #type: ignore
    lineTypes: bpy.props.EnumProperty(items = lineTypesArray, description= "Line types") #type: ignore
    lineWidths: bpy.props.EnumProperty(items = lineWidthsArray, description= "Line width") #type: ignore
    hatchesTypes: bpy.props.EnumProperty(items = hatchesArray, description= "Hatch type") #type: ignore
    #continueMode: bpy.props.BoolProperty(name="continueMode",default = False) #type: ignore
    #ignoreMid
    ignoreMid: bpy.props.BoolProperty(name="ignoreMid",default = False) #type: ignore

blender_classes = [VIEW3D_PT_dimensions,
                lines_operators.MESH_OT_lines,
                lines_operators.MESH_OT_lines_clear,
                dim_two_vert_op.MESH_OT_dimension_two_vert,
                dim_realtime_op.MESH_OT_realtime_dimension,
                DIMENSION_GLOBALS,
                cameras_setup.CAMERA_DIMSELECT,
                cameras_setup.CAMERA_DimSetupCam,
                hatches_operator.MESH_OT_hatches,
                dim_remake_op.MESH_OT_remake_dimension]

def register():
    for blender_class in blender_classes:
        bpy.utils.register_class(blender_class)

    bpy.types.Scene.DIMENSION = bpy.props.PointerProperty(type=DIMENSION_GLOBALS)
     
def unregister():
    del bpy.types.Scene.DIMENSION

    for blender_class in blender_classes:
        bpy.utils.unregister_class(blender_class)        
    
#if __name__ == "__main__": #if running from editor inside blender
    #register()
        
    #def invoke(self, context, event):
        #...
        
    #def modal(self, context, event):
        #...
    
    