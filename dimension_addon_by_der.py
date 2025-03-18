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

#version: 1.0.7

from . import cameras_setup
from . import hatches_operator
from . import lines_operators
import bpy # type: ignore
import bmesh # type: ignore
import math # type: ignore
import mathutils # type: ignore
import bpy_extras.view3d_utils # type: ignore
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
        propsTe = col.operator('mesh.dimensiontwovert', text = 'Dimension from 2 vertices')
        propsTe.boolFromModal = False
        propsTe.boolFirstRun = True

        col.operator('dimension.create', text = 'Realtime(mouse) dimensions')

        col = layout.column(align=True)
        col.operator('mesh.remakedimension', text = 'Remake dimension(load settings)')

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
        col.operator('mesh.linesclear', text = 'Clear thickness')

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

class MESH_OT_dimension_two_vert(bpy.types.Operator):
    """Add dimensions from two selected vertices."""
    bl_idname = "mesh.dimensiontwovert"
    bl_label = "Dimension"
    bl_options = {'REGISTER', 'UNDO'}

    debug = False
    timeItStart = 0.0
    timeItStop = 0.0

    otocit: bpy.props.BoolProperty(name="switch sides",description="switch to other side",default = False,) # type: ignore
    odsazeniHlavni: bpy.props.FloatProperty(name="dimension offset",description="distance of mine line",default=1.4,min = 0,step=1, precision= 3) # type: ignore
    odsazeniZakladna: bpy.props.FloatProperty(name="perpendicular lines bottom offset",description="distance from base",default=0.4,min = 0,step=1, precision= 3) # type: ignore
    presahKolmice: bpy.props.FloatProperty(name="perpendicular lines top length",description="distance above main line",default=0.6,min = 0,step=1, precision= 3) # type: ignore
    pocetDesetMist: bpy.props.IntProperty(name="decimal places",description="number of decimal places",default = 3,min = 0, max = 6) # type: ignore
    textOffset: bpy.props.FloatProperty(name="offset from main line",description="text distance from baseline",default = 0,step=1, precision= 3) # type: ignore
    textOffsetHor: bpy.props.FloatProperty(name="side offset from center",description="text offset from baseline center",default = 0,step=1, precision= 3) # type: ignore
    rotace: bpy.props.IntProperty(name="rotation along base",description="rotate dimension",default = 0,min = -180,max = 180,) # type: ignore
    textRotace: bpy.props.IntProperty(name="rotation along center",description="rotate text",default = 0,min = -180,max = 180,) # type: ignore
    tloustka: bpy.props.FloatProperty(name="line width",description="line width",default=0.1,min = 0,step=1, precision= 3) # type: ignore
    delkaSikmeCar: bpy.props.FloatProperty(name="border sign size",description="border sign size",default=1,min=0,step=1, precision= 3) # type: ignore
    textSize: bpy.props.FloatProperty(name="text size",description="text size",default=1,min=0,step=1, precision= 3) # type: ignore
    distanceScale: bpy.props.FloatProperty(name="scale for distance calc",description="scale for distance calculation",default = 1,min = 0,step=1, precision= 3) # type: ignore
    protazeni: bpy.props.FloatProperty(name="overlap length",description="length of overlap",default=1,min = 0,step=1, precision= 3) # type: ignore

    boolFromModal: bpy.props.BoolProperty(default = False, options={'HIDDEN'}) # type: ignore

    boolFirstRun: bpy.props.BoolProperty(default = True, options={'HIDDEN'}) # type: ignore

    boolRemakeOP: bpy.props.BoolProperty(default = False, options={'HIDDEN'}) # type: ignore

    bod1: bpy.props.FloatVectorProperty(options={'HIDDEN'}) # type: ignore
    bod2: bpy.props.FloatVectorProperty(options={'HIDDEN'}) # type: ignore

    #asi nepotrebne
    odsazeniHlavniHelpFR = 0.0
    odsazeniZakladnaHelpFR = 0.0
    zalohaOdsazeniZakladna = 0.0

    realtimeFinalDraw: bpy.props.BoolProperty(default = False, options={'HIDDEN'}) # type: ignore
    mouseMoved: bpy.props.BoolProperty(default = False, options={'HIDDEN'}) # type: ignore
    continueMode: bpy.props.BoolProperty(default = False, options={'HIDDEN'}) # type: ignore

    unitsHelpTemp = ''
    unitsBoolHelpTemp = False
    fontHelpTemp = ''
    rewriteRedoHelpTemp = False
    scaleHelpTemp = 100
    dimTypeTempHelp = ''

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def execute(self, context):

        #bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.ed.undo_push()

        bpy.context.area.tag_redraw()

        zalohaodsazeniHlavni = self.odsazeniHlavni
        zalohaodsazeniZakladna = self.odsazeniZakladna
        zalohaOtocit = self.otocit

        #nastavime vsechny propertis komplet podle UI - extra funkce - do UI jeste bool na prepisovani nastaveni z UNDO panelu
        if context.scene.DIMENSION.ignoreUndo == True:
            if self.boolFirstRun == True:
                #print('first')
                if self.boolRemakeOP == False:
                    self.setupPropsByUI(context)
                    self.boolRemakeOP = False
                else:
                    self.boolRemakeOP = False
                #tohle je ciste extra pro edit mode, kdy pri not boolFirstRun nacitame zmeny UI oproti tomu co je v UNDO
                self.unitsHelpTemp = context.scene.DIMENSION.jednotky
                #nastavim jednotky...
                self.setupUnitsScale(context)
                self.unitsBoolHelpTemp = context.scene.DIMENSION.showUnits
                self.fontHelpTemp = context.scene.DIMENSION.fontsArray
                self.rewriteRedoHelpTemp = context.scene.DIMENSION.ignoreUndo
                self.scaleHelpTemp = context.scene.DIMENSION.scale
                self.dimTypeTempHelp = context.scene.DIMENSION.dimType
            else:
                context.scene.DIMENSION.jednotky = self.unitsHelpTemp
                #nastavim jednotky...
                #self.setupUnitsScale(context)
                context.scene.DIMENSION.showUnits = self.unitsBoolHelpTemp
                context.scene.DIMENSION.fontsArray = self.fontHelpTemp
                context.scene.DIMENSION.ignoreUndo = self.rewriteRedoHelpTemp
                context.scene.DIMENSION.scale = self.scaleHelpTemp
                context.scene.DIMENSION.dimType = self.dimTypeTempHelp
            self.boolFirstRun = False
            #self.report({'ERROR'}, "zprava")
        
        if self.boolFirstRun == True:
            #print('first')
            #self.setupPropsByUI(context)
            #tohle je ciste extra pro edit mode, kdy pri not boolFirstRun nacitame zmeny UI oproti tomu co je v UNDO
            self.unitsHelpTemp = context.scene.DIMENSION.jednotky
            #nastavim jednotky...
            self.setupUnitsScale(context)
            self.unitsBoolHelpTemp = context.scene.DIMENSION.showUnits
            self.fontHelpTemp = context.scene.DIMENSION.fontsArray
            self.rewriteRedoHelpTemp = context.scene.DIMENSION.ignoreUndo
            self.scaleHelpTemp = context.scene.DIMENSION.scale
            self.dimTypeTempHelp = context.scene.DIMENSION.dimType
        else:
            context.scene.DIMENSION.jednotky = self.unitsHelpTemp
            #nastavim jednotky...
            #self.setupUnitsScale(context)
            context.scene.DIMENSION.showUnits = self.unitsBoolHelpTemp
            context.scene.DIMENSION.fontsArray = self.fontHelpTemp
            context.scene.DIMENSION.ignoreUndo = self.rewriteRedoHelpTemp
            context.scene.DIMENSION.scale = self.scaleHelpTemp
            context.scene.DIMENSION.dimType = self.dimTypeTempHelp
        self.boolFirstRun = False
        self.boolRemakeOP = False
        
        #switchRemakeBack
        #if self.boolRemakeOP == True:
            #self.boolRemakeOP = False

        #print(self.realtimeFinalDraw)
        #print(self.mouseMoved)

        if self.continueMode == True:
            self.odsazeniHlavni = zalohaodsazeniHlavni
            self.odsazeniZakladna = zalohaodsazeniZakladna
            self.otocit = zalohaOtocit

        if self.realtimeFinalDraw == True and self.mouseMoved == True: 
            self.odsazeniHlavni = zalohaodsazeniHlavni
            self.odsazeniZakladna = zalohaodsazeniZakladna
            self.otocit = zalohaOtocit
            pass


        countObjektu = 0
        selectedObject = None
        for object in context.selected_objects:
            countObjektu = countObjektu + 1
            selectedObject = object

        #print('local', self.boolFromModal)
        if countObjektu == 0:
            if self.boolFromModal == False:
                self.report({'ERROR'}, "No object selected")
                return {'CANCELLED'}
        
        if countObjektu > 1:
            self.report({'ERROR'}, "Too many objects selected")
            return {'CANCELLED'}

        #if self.boolFromModal == False: ? predavame boolFromModalTrue a no object selected, takze REDO pokud respektuje stav, tak vlastne ta sama situace nastava pri uplne nove kote bez selected object.....

        #doplnit popup nejakej pro malo nebo hodne vertice
        #ulozit pozici cursoru a na konci obnovit
        puvodniPoziceCursoru = bpy.context.scene.cursor.location.copy()

        objectMesh = None

        modeSwitch = False
        noObject = False
        if bpy.context.active_object == None:
            noObject = True
        if bpy.context.active_object != None: #realtime predavat kdyz je vsechno deselect a tim se bude nastavovat vert na bod1 a bod2
            if bpy.context.active_object.mode == 'EDIT':
                modeSwitch = True
                bpy.ops.object.mode_set(mode='OBJECT')

            objectMesh = bpy.context.active_object.data
            puvodniObjekt = bpy.context.active_object
            maticeGlobal = puvodniObjekt.matrix_world

        #tady vytahneme 2 vertices
        counter = 0
        pocetVert = 0
        predchozi = False
        verticeJedna = [0.0,0.0,0.0]
        verticeDva = [0.0,0.0,0.0]
        if self.boolFromModal == True:
            for i in range(3):
                verticeJedna[i]=self.bod1[i]
                verticeDva[i]=self.bod2[i]
        else:
            for vert in objectMesh.vertices:
                pocetVert = pocetVert + 1
                if counter > 2: 
                    self.report({'ERROR'}, "Too many vertices selected")
                    if modeSwitch == True:
                        bpy.ops.object.mode_set(mode='EDIT')
                    return {'CANCELLED'}
                if vert.select:
                    globCo = maticeGlobal @ vert.co
                    counter = counter + 1
                    if predchozi == False:
                        predchozi = True
                        verticeJedna[0] = globCo[0] 
                        verticeJedna[1] = globCo[1] 
                        verticeJedna[2] = globCo[2] 
                    else:
                        verticeDva[0] = globCo[0] 
                        verticeDva[1] = globCo[1] 
                        verticeDva[2] = globCo[2]             
            if counter < 2:    
                self.report({'ERROR'}, "Too little vertices selected")
                if modeSwitch == True:
                    bpy.ops.object.mode_set(mode='EDIT')
                return {'CANCELLED'}

        #otoci vektor podle user selection - ma vliv na kterou stranu se vykresli kota
        if self.otocit == True:
            tmpVekt = verticeJedna
            verticeJedna = verticeDva
            verticeDva = tmpVekt

        # budu muset osetrit kazdou rovinu zvlast po vypocetni smeroveho vektoru, respektive 2 nulove vektory - to bude nejcastejsi a pak ifka pro prostor Z - NETREBA
        listveci = [verticeJedna,verticeDva]

        if context.scene.DIMENSION.dimType == 'Slope':
            listKotaText = self.vytvorKotuSlope()
            self.osadKotuSlope(listKotaText, listveci)
            #self.srovnejRotationEulerObjektum(listKotaText[0], listKotaText[1], listveci)
        if context.scene.DIMENSION.dimType == 'Slope no overlap':
            listKotaText = self.vytvorKotuSlopeNo()  
            self.osadKotuSlopeNo(listKotaText, listveci)
            #self.srovnejRotationEulerObjektum(listKotaText[0], listKotaText[1], listveci)
        if context.scene.DIMENSION.dimType == 'Arrow open':
            listKotaText = self.vytvorKotuArrowOpen()
            self.osadKotuArrowOpen(listKotaText, listveci)
            #self.srovnejRotationEulerObjektum(listKotaText[0], listKotaText[1], listveci)
        if context.scene.DIMENSION.dimType == 'Arrow in':  
            listKotaText = self.vytvorKotuArrowIn()
            self.osadKotuArrowIn(listKotaText, listveci)
            #self.srovnejRotationEulerObjektum(listKotaText[0], listKotaText[1], listveci)
        if context.scene.DIMENSION.dimType == 'Arrow out':
            listKotaText = self.vytvorKotuArrowOut()
            self.osadKotuArrowOut(listKotaText, listveci)
            #self.srovnejRotationEulerObjektum(listKotaText[0], listKotaText[1], listveci)

        if modeSwitch == True:
            bpy.context.view_layer.objects.active = puvodniObjekt
            bpy.ops.object.select_all(action='DESELECT')
            puvodniObjekt.select_set(True)
            bpy.ops.object.mode_set(mode='EDIT')

        bpy.context.scene.cursor.location = puvodniPoziceCursoru

        if noObject == True:
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = None

        self.globalsSave()

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(self, "otocit")
        row = layout.row()
        row.label(text = "Dimension settings:")
        row = layout.row()
        row.prop(self, "odsazeniHlavni")
        row = layout.row()
        row.prop(self, "odsazeniZakladna")
        row = layout.row()
        row.prop(self, "delkaSikmeCar")
        row = layout.row()
        row.prop(self, "tloustka")
        row = layout.row()
        row.prop(self, "presahKolmice")
        if context.scene.DIMENSION.dimType == 'Slope':
            row = layout.row()
            row.prop(self, "protazeni")

        row = layout.row()
        row.prop(self, "rotace")


        row = layout.row()
        row.label(text = "Number settings:")
        row = layout.row()
        row.prop(self, "textSize")
        row = layout.row()
        row.prop(self, "pocetDesetMist")
        row = layout.row()
        row.prop(self, "textOffset")
        row = layout.row()
        row.prop(self, "textOffsetHor")
        row = layout.row()
        row.prop(self, "textRotace")
        row = layout.row()
        row.prop(self, "distanceScale")

    def setupPropsByUI(self,context):
        #DPI a papir daji dohromady rozliseni - resime jenom vetsi rozmer A5-210 A4-297 A3-420 A2-594 A1-841 A0-1189
        self.rotace = 0
        self.textRotace = 0
        self.otocit = False
        self.tloustka = 0.00028*context.scene.DIMENSION.scale
        self.protazeni = 0.0012*context.scene.DIMENSION.scale
        self.odsazeniHlavni = 0.006*context.scene.DIMENSION.scale
        self.odsazeniZakladna = 0.002*context.scene.DIMENSION.scale
        self.presahKolmice = 0.0012*context.scene.DIMENSION.scale
        self.meritko = context.scene.DIMENSION.scale
        self.delkaSikmeCar = 0.0024*context.scene.DIMENSION.scale
        self.textSize = 0.0036*context.scene.DIMENSION.scale
        if context.scene.DIMENSION.jednotky == 'mm':
            self.distanceScale = 1000
            self.pocetDesetMist = 0
        if context.scene.DIMENSION.jednotky == 'cm':
            self.distanceScale = 100
            self.pocetDesetMist = 2
        if context.scene.DIMENSION.jednotky == 'dm':
            self.distanceScale = 10
            self.pocetDesetMist = 1
        if context.scene.DIMENSION.jednotky == 'm' or context.scene.DIMENSION.jednotky == 'None':
            self.distanceScale = 1
            self.pocetDesetMist = 3
        if context.scene.DIMENSION.jednotky == 'km':
            self.distanceScale = 0.001
            self.pocetDesetMist = 4
        if context.scene.DIMENSION.jednotky == 'ft in':
            self.distanceScale = 1
            self.pocetDesetMist = 0
        if context.scene.DIMENSION.jednotky == 'inches':
            self.distanceScale = 1
            self.pocetDesetMist = 0
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
        context.scene.DIMENSION.rotaceTextuG = self.textRotace
        context.scene.DIMENSION.tloustkaG = self.tloustka
        context.scene.DIMENSION.delkaSikmeCarG = self.delkaSikmeCar
        context.scene.DIMENSION.textSizeG = self.textSize
        context.scene.DIMENSION.distanceScaleG = self.distanceScale

    def vytvorKotuArrowOut(self) -> bpy.types.Object:

        context = bpy.context

        zalohaCursoru = context.scene.cursor.location.copy()
        zalohaRotaceCusoru = context.scene.cursor.rotation_euler.copy()

        #vytvorime novy objekt
        for porad in range(3):
            context.scene.cursor.location[porad] = 0
            context.scene.cursor.rotation_euler[porad] = 0


        #prihodime text
        bpy.ops.object.text_add()
        objectTextu = context.active_object
        self.ObjektTextu = objectTextu
        objectTextu.data.font = bpy.data.fonts[context.scene.DIMENSION.fontsArray]

        #bpy.ops.mesh.primitive_vert_add()
        bpy.ops.mesh.primitive_plane_add()

        objectKoty = context.active_object
        self.ObjektKoty = objectKoty
        objNameBase = 'dimension.'
        objName = 'dimension'
        counter = 1
        boolZapsano = False
        while boolZapsano == False:
            if bpy.data.objects.get(objName):
                #jmeno zabrano, pridavame + 1
                objName = objNameBase + str(counter)
                counter = counter + 1
            else:
                context.active_object.name = objName
                boolZapsano = True

        objectMesh = context.active_object.data
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.delete(type='EDGE_FACE') #pridana plane ma vsechno selected
        bpy.ops.object.mode_set(mode='OBJECT')

        objectMesh.vertices.add(26)

        for vert in objectMesh.vertices:
            vert.select = False

        bFA=bmesh.new()   
        bFA.from_mesh(objectMesh)
        bFA.verts.ensure_lookup_table()
        listVert = [bFA.verts[0],bFA.verts[4],bFA.verts[7],bFA.verts[1]] 
        vertsSequence = [bFA.verts[0],bFA.verts[1],bFA.verts[6],bFA.verts[5]] 
        #bmesh.ops.contextual_create(bFA, geom=listVert)
        bFA.faces.new(vertsSequence)
        bFA.faces.new(listVert)
        listVert = [bFA.verts[0],bFA.verts[5],bFA.verts[11],bFA.verts[10]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[0],bFA.verts[10],bFA.verts[12],bFA.verts[2]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[0],bFA.verts[2],bFA.verts[23],bFA.verts[24]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[0],bFA.verts[24],bFA.verts[22],bFA.verts[3]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[0],bFA.verts[3],bFA.verts[18],bFA.verts[16]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[0],bFA.verts[16],bFA.verts[17],bFA.verts[4]]
        bFA.faces.new(listVert)

        listVert = [bFA.verts[1],bFA.verts[9],bFA.verts[14],bFA.verts[13]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[1],bFA.verts[13],bFA.verts[15],bFA.verts[6]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[1],bFA.verts[7],bFA.verts[21],bFA.verts[19]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[1],bFA.verts[19],bFA.verts[20],bFA.verts[8]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[1],bFA.verts[8],bFA.verts[25],bFA.verts[27]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[1],bFA.verts[27],bFA.verts[26],bFA.verts[9]]
        bFA.faces.new(listVert)

        bFA.to_mesh(objectMesh)
        bFA.free()  

        #pridame material
        #testuju jestli material existuje
        material = None
        matNoneB = True
        for mat in bpy.data.materials:
            if mat.name == 'ColorBaseMat':
                material = mat
                matNoneB = False
                break
        if matNoneB == True:
            material = bpy.data.materials.new('ColorBaseMat')
            material.use_nodes = True
            material.node_tree.nodes.remove(material.node_tree.nodes["Principled BSDF"])
            emNode = material.node_tree.nodes.new('ShaderNodeEmission')
            emNode.inputs[0].default_value = 0,0,0,1
            material.node_tree.links.new(emNode.outputs[0],material.node_tree.nodes[0].inputs[0])

        objectKoty.data.materials.append(material)
        objectTextu.data.materials.append(material)

        #context.view_layer.objects.active = objectKoty
        objectTextu.select_set(True)
        bpy.ops.object.parent_set(type='OBJECT', xmirror=False, keep_transform=True)

        context.scene.cursor.location = zalohaCursoru
        context.scene.cursor.rotation_euler = zalohaRotaceCusoru

        return [objectKoty,objectTextu]
    
    def osadKotuArrowOut(self, listKotaText, listVeci) -> bpy.types.Object:

        context = bpy.context

        zalohaCursoru = context.scene.cursor.location.copy()

        for porad in range(3):
            context.scene.cursor.location[porad] = 0

        objectKoty = listKotaText[0]

        self.ObjektKoty = objectKoty

        kotaBaseVert1 = listVeci[0]
        kotaBaseVert2 = listVeci[1]
        
        objectMesh = objectKoty.data
        pocetVert = 0

        if len(listVeci) > 2:
            self.odsazeniZakladna = self.zalohaOdsazeniZakladna
            self.odsazeniHlavni = listVeci[2]
            self.zalohaOdsazeniZakladna = self.odsazeniZakladna
            self.odsazeniZakladna = self.odsazeniZakladna + listVeci[3]

        #ziskame stred koty a posuneme object koty na tyto souradnice
        stredKoty = self.vratBodMeziDvemaBody(kotaBaseVert1, kotaBaseVert2) #stred koty uvnitr objektu
        for porad in range(3):
            objectKoty.location[porad] = stredKoty[porad]

        #nastavime rotaci koty podle vektoru
        self.rotaceDvaBody(objectKoty, kotaBaseVert1, kotaBaseVert2)

        #prepocitame vychozi body z world na local posunute a natocene koty
        kotaBaseVert1WorldBackUp = kotaBaseVert1
        kotaBaseVert2WorldBackUp = kotaBaseVert2
        bpy.context.view_layer.update()
        world_matrix_inv = objectKoty.matrix_world.inverted()
        kotaBaseVert1 = world_matrix_inv @ mathutils.Vector((kotaBaseVert1WorldBackUp[0], kotaBaseVert1WorldBackUp[1], kotaBaseVert1WorldBackUp[2]))
        kotaBaseVert2 = world_matrix_inv @ mathutils.Vector((kotaBaseVert2WorldBackUp[0], kotaBaseVert2WorldBackUp[1], kotaBaseVert2WorldBackUp[2]))

        kotaBaseVert1Original = kotaBaseVert1
        kotaBaseVert2Original = kotaBaseVert2

        zvetseniZnaku = 1.4

        #prvni body koty - vpravo
        kotaBaseVert1 = self.pripoctiY(kotaBaseVert1, self.odsazeniHlavni) #odsazujeme prvni body od zakladny dle jednotky, osa 2 je svisla nulova... to se musi doplnit jestli chceme podporu boku nejak... 
        objectMesh.vertices[pocetVert].co = kotaBaseVert1
        kotaBaseVert2 = self.pripoctiY(kotaBaseVert2, self.odsazeniHlavni)
        pocetVert += 1
        objectMesh.vertices[pocetVert].co = kotaBaseVert2
        #body prodlouzeni
        pocetVert += 1
        kotaBaseVert1prodl = self.pripoctiX(objectMesh.vertices[0].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = kotaBaseVert1prodl
        kotaBaseVert1prodl = self.pripoctiY(objectMesh.vertices[pocetVert].co, -self.tloustka/2)
        objectMesh.vertices[pocetVert].co = kotaBaseVert1prodl
        pocetVert += 1
        kotaBaseVert1prodl = self.pripoctiX(objectMesh.vertices[0].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = kotaBaseVert1prodl
        kotaBaseVert1prodl = self.pripoctiY(objectMesh.vertices[pocetVert].co, self.tloustka/2)
        objectMesh.vertices[pocetVert].co = kotaBaseVert1prodl

        #2 kolem hlavni vpravo
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[0].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1 = self.pripoctiY(objectMesh.vertices[pocetVert].co, self.tloustka/2)
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[0].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1 = self.pripoctiY(objectMesh.vertices[pocetVert].co, -self.tloustka/2)
        objectMesh.vertices[pocetVert].co = bodSirky1

        #4 kolem hlavni vlevo
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[1].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1 = self.pripoctiY(objectMesh.vertices[pocetVert].co, -self.tloustka/2)
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiY(objectMesh.vertices[6].co, self.tloustka)
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[7].co, -self.tloustka)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[6].co, -self.tloustka)  
        objectMesh.vertices[pocetVert].co = bodSirky1

        #spodni vpravo - stred,vlevo,vpravo
        pocetVert += 1
        kotaKolmiceSpodek1 = self.pripoctiY(kotaBaseVert1Original, self.odsazeniZakladna)
        objectMesh.vertices[pocetVert].co = kotaKolmiceSpodek1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 1].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 2].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1

        #spodni vlevo - stred,vlevo,vpravo
        pocetVert += 1
        kotaKolmiceSpodek2 = self.pripoctiY(kotaBaseVert2Original, self.odsazeniZakladna)
        objectMesh.vertices[pocetVert].co = kotaKolmiceSpodek2
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 1].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 2].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1

        #horni vpravo - stred,vlevo,vpravo
        pocetVert += 1
        kotaKolmiceVrsek1 = self.pripoctiY(objectMesh.vertices[0].co, self.presahKolmice)
        objectMesh.vertices[pocetVert].co = kotaKolmiceVrsek1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 1].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 2].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1

        #horni vlevo - stred,vlevo,vpravo
        pocetVert += 1
        kotaKolmiceVrsek2 = self.pripoctiY(objectMesh.vertices[1].co, self.presahKolmice)
        objectMesh.vertices[pocetVert].co = kotaKolmiceVrsek2
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 1].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 2].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vpravo horni 
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[3].co,math.sin(15/(180/math.pi))*(self.delkaSikmeCar/2 * zvetseniZnaku))
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1=self.pripoctiX(objectMesh.vertices[pocetVert].co,math.cos(15/(180/math.pi))*(self.delkaSikmeCar/2 * zvetseniZnaku))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vpravo spodni
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[2].co,-math.sin(15/(180/math.pi))*(self.delkaSikmeCar/2 * zvetseniZnaku))
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1=self.pripoctiX(objectMesh.vertices[pocetVert].co,math.cos(15/(180/math.pi))*(self.delkaSikmeCar/2 * zvetseniZnaku))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vpravo stred
        pocetVert +=1
        bodSirky1=self.pripoctiX(objectMesh.vertices[0].co,((self.tloustka/2)+ (math.cos(15/(180/math.pi))*(self.delkaSikmeCar/2*zvetseniZnaku))))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vlevo horni 
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[8].co,math.sin(15/(180/math.pi))*(self.delkaSikmeCar/2 * zvetseniZnaku))
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1=self.pripoctiX(objectMesh.vertices[pocetVert].co,-math.cos(15/(180/math.pi))*(self.delkaSikmeCar/2 * zvetseniZnaku))
        objectMesh.vertices[pocetVert].co = bodSirky1
        #sikmina vlevo spodni 
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[9].co,-math.sin(15/(180/math.pi))*(self.delkaSikmeCar/2 * zvetseniZnaku))
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1=self.pripoctiX(objectMesh.vertices[pocetVert].co,-math.cos(15/(180/math.pi))*(self.delkaSikmeCar/2 * zvetseniZnaku))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vlevo stred
        pocetVert +=1
        bodSirky1=self.pripoctiX(objectMesh.vertices[1].co,-((self.tloustka/2)+ (math.cos(15/(180/math.pi))*(self.delkaSikmeCar/2*zvetseniZnaku))))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #orig snap points
        pocetVert +=1   
        bodSirky1=kotaBaseVert1Original
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert +=1   
        bodSirky1=kotaBaseVert2Original
        objectMesh.vertices[pocetVert].co = bodSirky1
        

        #prihodime text
        objectTextu = listKotaText[1]
        self.ObjektTextu = objectTextu

        #ted vlastne pricteme location
        stredKotyOdsaz = self.vratBodMeziDvemaBody(kotaBaseVert1, kotaBaseVert2)
        #objectTextu.location = [0.0,0.0,0.0]
        #objectTextu.rotation_euler = [0.0,0.0,0.0]
        for porad in range(3):
            objectTextu.location[porad] = stredKotyOdsaz[porad]

        #nastavime rotaci koty podle vektoru
        self.rotaceDvaBody(objectTextu, kotaBaseVert1, kotaBaseVert2)

        KotaNumber = self.vzdalenostMeziDvemaBody(kotaBaseVert1,kotaBaseVert2)
        KotaNumber = KotaNumber * self.distanceScale
        #tady uz bych to mohl oddelit podle ft in a metric
        if context.scene.DIMENSION.jednotky == 'ft in':
            textKoty = self.makeImperial(context, KotaNumber)
        elif context.scene.DIMENSION.jednotky == 'inches':
            textKoty = self.makeInches(context, KotaNumber)
        else:
            textKoty = str(round(KotaNumber, self.pocetDesetMist))
            textKoty = self.zaokrouhlNa(textKoty, self.pocetDesetMist)
            textKoty = self.vymenTeckuZaCarku(textKoty)
            textJednotek = context.scene.DIMENSION.jednotky
            if context.scene.DIMENSION.jednotky != 'None' and context.scene.DIMENSION.showUnits == True:
                textKoty = textKoty + ' ' + textJednotek
        
        #print(textKoty)
        objectTextu.data.body = textKoty
        objectTextu.data.align_x = 'CENTER'
        objectTextu.data.align_y = 'BOTTOM'
        objectTextu.data.offset_y = self.textOffset
        objectTextu.data.offset_x = self.textOffsetHor
        objectTextu.data.size = self.textSize

        #no a ted uz muzeme tocit na x
        objectTextu.rotation_euler.rotate_axis("Z", math.radians(self.textRotace))

        if math.isclose(objectTextu.rotation_euler[2], objectKoty.rotation_euler[2], abs_tol=0.001) == False: #tohle jenom dorovnava 360 stupnu na Z v pripadech kdy je to otocene o celych 360
            objectTextu.rotation_euler[2] = objectTextu.rotation_euler[2] + 2*math.pi

        objectKoty.rotation_euler[0] = math.radians(self.rotace)

        objectTextu.select_set(False)
        objectKoty.select_set(False)

        context.scene.cursor.location = zalohaCursoru

        return 
    
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

    def vytvorKotuArrowIn(self) -> bpy.types.Object:

        context = bpy.context

        zalohaCursoru = context.scene.cursor.location.copy()
        zalohaRotaceCusoru = context.scene.cursor.rotation_euler.copy()

        #vytvorime novy objekt
        for porad in range(3):
            context.scene.cursor.location[porad] = 0
            context.scene.cursor.rotation_euler[porad] = 0

        #prihodime text
        bpy.ops.object.text_add()
        objectTextu = context.active_object
        self.ObjektTextu = objectTextu
        objectTextu.data.font = bpy.data.fonts[context.scene.DIMENSION.fontsArray]

        #bpy.ops.mesh.primitive_vert_add()
        bpy.ops.mesh.primitive_plane_add()

        objectKoty = context.active_object
        self.ObjektKoty = objectKoty
        objNameBase = 'dimension.'
        objName = 'dimension'
        counter = 1
        boolZapsano = False
        while boolZapsano == False:
            if bpy.data.objects.get(objName):
                #jmeno zabrano, pridavame + 1
                objName = objNameBase + str(counter)
                counter = counter + 1
            else:
                context.active_object.name = objName
                boolZapsano = True

        objectMesh = context.active_object.data
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.delete(type='EDGE_FACE') #pridana plane ma vsechno selected
        bpy.ops.object.mode_set(mode='OBJECT')

        objectMesh.vertices.add(26)

        for vert in objectMesh.vertices:
            vert.select = False
        
        bFA=bmesh.new()   
        bFA.from_mesh(objectMesh)
        bFA.verts.ensure_lookup_table()
        listVert = [bFA.verts[0],bFA.verts[4],bFA.verts[6],bFA.verts[1]] 
        vertsSequence = [bFA.verts[0],bFA.verts[1],bFA.verts[7],bFA.verts[5]] 
        #bmesh.ops.contextual_create(bFA, geom=listVert)
        bFA.faces.new(vertsSequence)
        bFA.faces.new(listVert)
        listVert = [bFA.verts[0],bFA.verts[5],bFA.verts[9],bFA.verts[8]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[0],bFA.verts[8],bFA.verts[10],bFA.verts[2]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[0],bFA.verts[2],bFA.verts[16],bFA.verts[14]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[0],bFA.verts[14],bFA.verts[15],bFA.verts[4]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[4],bFA.verts[20],bFA.verts[22]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[5],bFA.verts[23],bFA.verts[21]]
        bFA.faces.new(listVert)

        listVert = [bFA.verts[1],bFA.verts[3],bFA.verts[12],bFA.verts[11]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[1],bFA.verts[11],bFA.verts[13],bFA.verts[7]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[7],bFA.verts[25],bFA.verts[27]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[6],bFA.verts[26],bFA.verts[24]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[1],bFA.verts[6],bFA.verts[19],bFA.verts[17]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[1],bFA.verts[17],bFA.verts[18],bFA.verts[3]]
        bFA.faces.new(listVert)

        bFA.to_mesh(objectMesh)
        bFA.free()  

        #pridame material
        #testuju jestli material existuje
        material = None
        matNoneB = True
        for mat in bpy.data.materials:
            if mat.name == 'ColorBaseMat':
                material = mat
                matNoneB = False
                break
        if matNoneB == True:
            material = bpy.data.materials.new('ColorBaseMat')
            material.use_nodes = True
            material.node_tree.nodes.remove(material.node_tree.nodes["Principled BSDF"])
            emNode = material.node_tree.nodes.new('ShaderNodeEmission')
            emNode.inputs[0].default_value = 0,0,0,1
            material.node_tree.links.new(emNode.outputs[0],material.node_tree.nodes[0].inputs[0])

        objectKoty.data.materials.append(material)
        objectTextu.data.materials.append(material)

        objectTextu.select_set(True)
        bpy.ops.object.parent_set(type='OBJECT', xmirror=False, keep_transform=True)

        context.scene.cursor.location = zalohaCursoru
        context.scene.cursor.rotation_euler = zalohaRotaceCusoru

        return [objectKoty,objectTextu]
    
    def osadKotuArrowIn(self, listKotaText, listVeci) -> bpy.types.Object:

        context = bpy.context

        zalohaCursoru = context.scene.cursor.location.copy()

        for porad in range(3):
            context.scene.cursor.location[porad] = 0

        objectKoty = listKotaText[0]

        self.ObjektKoty = objectKoty

        kotaBaseVert1 = listVeci[0]
        kotaBaseVert2 = listVeci[1]
        
        objectMesh = objectKoty.data
        pocetVert = 0

        if len(listVeci) > 2:
            self.odsazeniZakladna = self.zalohaOdsazeniZakladna
            self.odsazeniHlavni = listVeci[2]
            self.zalohaOdsazeniZakladna = self.odsazeniZakladna
            self.odsazeniZakladna = self.odsazeniZakladna + listVeci[3]

        #ziskame stred koty a posuneme object koty na tyto souradnice
        stredKoty = self.vratBodMeziDvemaBody(kotaBaseVert1, kotaBaseVert2) #stred koty uvnitr objektu
        for porad in range(3):
            objectKoty.location[porad] = stredKoty[porad]

        #nastavime rotaci koty podle vektoru
        self.rotaceDvaBody(objectKoty, kotaBaseVert1, kotaBaseVert2)

        #prepocitame vychozi body z world na local posunute a natocene koty
        kotaBaseVert1WorldBackUp = kotaBaseVert1
        kotaBaseVert2WorldBackUp = kotaBaseVert2
        bpy.context.view_layer.update()
        world_matrix_inv = objectKoty.matrix_world.inverted()
        kotaBaseVert1 = world_matrix_inv @ mathutils.Vector((kotaBaseVert1WorldBackUp[0], kotaBaseVert1WorldBackUp[1], kotaBaseVert1WorldBackUp[2]))
        kotaBaseVert2 = world_matrix_inv @ mathutils.Vector((kotaBaseVert2WorldBackUp[0], kotaBaseVert2WorldBackUp[1], kotaBaseVert2WorldBackUp[2]))

        kotaBaseVert1Original = kotaBaseVert1
        kotaBaseVert2Original = kotaBaseVert2

        zvetseniZnaku = 1.4

        #prvni body koty - vpravo
        kotaBaseVert1 = self.pripoctiY(kotaBaseVert1, self.odsazeniHlavni) #odsazujeme prvni body od zakladny dle jednotky, osa 2 je svisla nulova... to se musi doplnit jestli chceme podporu boku nejak... 
        objectMesh.vertices[pocetVert].co = kotaBaseVert1
        kotaBaseVert2 = self.pripoctiY(kotaBaseVert2, self.odsazeniHlavni)
        pocetVert += 1
        objectMesh.vertices[pocetVert].co = kotaBaseVert2

        #body prodlouzeni
        pocetVert += 1
        kotaBaseVert1prodl = self.pripoctiX(objectMesh.vertices[0].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = kotaBaseVert1prodl
        pocetVert += 1
        kotaBaseVert2prodl = self.pripoctiX(objectMesh.vertices[1].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = kotaBaseVert2prodl

        #2 kolem hlavni vpravo
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[0].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1 = self.pripoctiY(objectMesh.vertices[pocetVert].co, self.tloustka/2)
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[0].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1 = self.pripoctiY(objectMesh.vertices[pocetVert].co, -self.tloustka/2)
        objectMesh.vertices[pocetVert].co = bodSirky1

        #2 kolem hlavni vlevo
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[1].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1 = self.pripoctiY(objectMesh.vertices[pocetVert].co, self.tloustka/2)
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiY(objectMesh.vertices[pocetVert - 1].co, -self.tloustka)
        objectMesh.vertices[pocetVert].co = bodSirky1

        #spodni vpravo - stred,vlevo,vpravo
        pocetVert += 1
        kotaKolmiceSpodek1 = self.pripoctiY(kotaBaseVert1Original, self.odsazeniZakladna)
        objectMesh.vertices[pocetVert].co = kotaKolmiceSpodek1

        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 1].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 2].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1

        #spodni vlevo - stred,vlevo,vpravo
        pocetVert += 1
        kotaKolmiceSpodek2 = self.pripoctiY(kotaBaseVert2Original, self.odsazeniZakladna)
        objectMesh.vertices[pocetVert].co = kotaKolmiceSpodek2
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 1].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 2].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1

        #horni vpravo - stred,vlevo,vpravo
        pocetVert += 1
        kotaKolmiceVrsek1 = self.pripoctiY(objectMesh.vertices[0].co, self.presahKolmice)
        objectMesh.vertices[pocetVert].co = kotaKolmiceVrsek1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 1].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 2].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1

        #horni vlevo - stred,vlevo,vpravo
        pocetVert += 1
        kotaKolmiceVrsek2 = self.pripoctiY(objectMesh.vertices[1].co, self.presahKolmice)
        objectMesh.vertices[pocetVert].co = kotaKolmiceVrsek2
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 1].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 2].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vpravo horni 
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[4].co,math.sin(15/(180/math.pi))*(self.delkaSikmeCar/2 * zvetseniZnaku))
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1=self.pripoctiX(objectMesh.vertices[pocetVert].co,-math.cos(15/(180/math.pi))*(self.delkaSikmeCar/2 * zvetseniZnaku))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vpravo spodni
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[5].co,-math.sin(15/(180/math.pi))*(self.delkaSikmeCar/2 * zvetseniZnaku))
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1=self.pripoctiX(objectMesh.vertices[pocetVert].co,-math.cos(15/(180/math.pi))*(self.delkaSikmeCar/2 * zvetseniZnaku))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vpravo horni spodek
        pocetVert +=1
        bodSirky1=self.pripoctiX(objectMesh.vertices[4].co,-math.cos(15/(180/math.pi))*(self.delkaSikmeCar/2 * zvetseniZnaku))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vpravo spodni vrsek
        pocetVert +=1
        bodSirky1=self.pripoctiX(objectMesh.vertices[5].co,-math.cos(15/(180/math.pi))*(self.delkaSikmeCar/2 * zvetseniZnaku))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vlevo horni 
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[6].co,math.sin(15/(180/math.pi))*(self.delkaSikmeCar/2 * zvetseniZnaku))
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1=self.pripoctiX(objectMesh.vertices[pocetVert].co,math.cos(15/(180/math.pi))*(self.delkaSikmeCar/2 * zvetseniZnaku))
        objectMesh.vertices[pocetVert].co = bodSirky1
        #sikmina vlevo spodni 
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[7].co,-math.sin(15/(180/math.pi))*(self.delkaSikmeCar/2 * zvetseniZnaku))
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1=self.pripoctiX(objectMesh.vertices[pocetVert].co,math.cos(15/(180/math.pi))*(self.delkaSikmeCar/2 * zvetseniZnaku))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vlevo horni spodek
        pocetVert +=1
        bodSirky1=self.pripoctiX(objectMesh.vertices[6].co,-math.cos(15/(180/math.pi))*(-self.delkaSikmeCar/2 * zvetseniZnaku))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vlevo spodni vrsek
        pocetVert +=1
        bodSirky1=self.pripoctiX(objectMesh.vertices[7].co,-math.cos(15/(180/math.pi))*(-self.delkaSikmeCar/2 * zvetseniZnaku))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #orig snap points
        pocetVert +=1   
        bodSirky1=kotaBaseVert1Original
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert +=1   
        bodSirky1=kotaBaseVert2Original
        objectMesh.vertices[pocetVert].co = bodSirky1

        #hodime text do objektu
        objectTextu = listKotaText[1]
        self.ObjektTextu = objectTextu

        #ted vlastne pricteme location
        stredKotyOdsaz = self.vratBodMeziDvemaBody(kotaBaseVert1, kotaBaseVert2)
        for porad in range(3):
            objectTextu.location[porad] = stredKotyOdsaz[porad]
            
        #nastavime rotaci koty podle vektoru
        self.rotaceDvaBody(objectTextu, kotaBaseVert1, kotaBaseVert2)

        KotaNumber = self.vzdalenostMeziDvemaBody(kotaBaseVert1,kotaBaseVert2)
        KotaNumber = KotaNumber * self.distanceScale
        #tady uz bych to mohl oddelit podle ft in a metric
        if context.scene.DIMENSION.jednotky == 'ft in':
            textKoty = self.makeImperial(context, KotaNumber)
        elif context.scene.DIMENSION.jednotky == 'inches':
            textKoty = self.makeInches(context, KotaNumber)
        else:
            textKoty = str(round(KotaNumber, self.pocetDesetMist))
            textKoty = self.zaokrouhlNa(textKoty, self.pocetDesetMist)
            textKoty = self.vymenTeckuZaCarku(textKoty)
            textJednotek = context.scene.DIMENSION.jednotky
            if context.scene.DIMENSION.jednotky != 'None' and context.scene.DIMENSION.showUnits == True:
                textKoty = textKoty + ' ' + textJednotek

        #print(textKoty)
        objectTextu.data.body = textKoty
        objectTextu.data.align_x = 'CENTER'
        objectTextu.data.align_y = 'BOTTOM'
        objectTextu.data.offset_y = self.textOffset
        objectTextu.data.offset_x = self.textOffsetHor
        objectTextu.data.size = self.textSize

        #no a ted uz muzeme tocit na x
        objectTextu.rotation_euler.rotate_axis("Z", math.radians(self.textRotace))

        if math.isclose(objectTextu.rotation_euler[2], objectKoty.rotation_euler[2], abs_tol=0.001) == False: #tohle jenom dorovnava 360 stupnu na Z v pripadech kdy je to otocene o celych 360
            objectTextu.rotation_euler[2] = objectTextu.rotation_euler[2] + 2*math.pi
        
        objectKoty.rotation_euler[0] = math.radians(self.rotace)

        objectTextu.select_set(False)
        objectKoty.select_set(False)

        context.scene.cursor.location = zalohaCursoru

        return
    
    def vytvorKotuArrowOpen(self) -> bpy.types.Object:

        context = bpy.context

        zalohaCursoru = context.scene.cursor.location.copy()
        zalohaRotaceCusoru = context.scene.cursor.rotation_euler.copy()

        #vytvorime novy objekt
        for porad in range(3):
            context.scene.cursor.location[porad] = 0
            context.scene.cursor.rotation_euler[porad] = 0

        #prihodime text
        bpy.ops.object.text_add()
        objectTextu = context.active_object
        self.ObjektTextu = objectTextu
        objectTextu.data.font = bpy.data.fonts[context.scene.DIMENSION.fontsArray]

        #bpy.ops.mesh.primitive_vert_add()
        bpy.ops.mesh.primitive_plane_add()

        objectKoty = context.active_object
        self.ObjektKoty = objectKoty
        objNameBase = 'dimension.'
        objName = 'dimension'
        counter = 1
        boolZapsano = False
        while boolZapsano == False:
            if bpy.data.objects.get(objName):
                #jmeno zabrano, pridavame + 1
                objName = objNameBase + str(counter)
                counter = counter + 1
            else:
                context.active_object.name = objName
                boolZapsano = True

        objectMesh = context.active_object.data
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.delete(type='EDGE_FACE') #pridana plane ma vsechno selected
        pocetVert = 0
        bpy.ops.object.mode_set(mode='OBJECT')

        objectMesh.vertices.add(30)

        for vert in objectMesh.vertices:
            vert.select = False
        
        bFA=bmesh.new()   
        bFA.from_mesh(objectMesh)
        bFA.verts.ensure_lookup_table()
        listVert = [bFA.verts[0],bFA.verts[4],bFA.verts[6],bFA.verts[1]] 
        vertsSequence = [bFA.verts[0],bFA.verts[1],bFA.verts[7],bFA.verts[5]] 
        #bmesh.ops.contextual_create(bFA, geom=listVert)
        bFA.faces.new(vertsSequence)
        bFA.faces.new(listVert)
        listVert = [bFA.verts[0],bFA.verts[5],bFA.verts[9],bFA.verts[8]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[0],bFA.verts[8],bFA.verts[10],bFA.verts[2]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[0],bFA.verts[2],bFA.verts[16],bFA.verts[14]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[0],bFA.verts[14],bFA.verts[15],bFA.verts[4]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[4],bFA.verts[20],bFA.verts[22],bFA.verts[24]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[5],bFA.verts[25],bFA.verts[23],bFA.verts[21]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[1],bFA.verts[3],bFA.verts[12],bFA.verts[11]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[1],bFA.verts[11],bFA.verts[13],bFA.verts[7]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[7],bFA.verts[27],bFA.verts[29],bFA.verts[31]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[6],bFA.verts[30],bFA.verts[28],bFA.verts[26]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[1],bFA.verts[6],bFA.verts[19],bFA.verts[17]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[1],bFA.verts[17],bFA.verts[18],bFA.verts[3]]
        bFA.faces.new(listVert)

        bFA.to_mesh(objectMesh)
        bFA.free()  

        #pridame material
        #testuju jestli material existuje
        material = None
        matNoneB = True
        for mat in bpy.data.materials:
            if mat.name == 'ColorBaseMat':
                material = mat
                matNoneB = False
                break
        if matNoneB == True:
            material = bpy.data.materials.new('ColorBaseMat')
            material.use_nodes = True
            material.node_tree.nodes.remove(material.node_tree.nodes["Principled BSDF"])
            emNode = material.node_tree.nodes.new('ShaderNodeEmission')
            emNode.inputs[0].default_value = 0,0,0,1
            material.node_tree.links.new(emNode.outputs[0],material.node_tree.nodes[0].inputs[0])

        objectKoty.data.materials.append(material)
        objectTextu.data.materials.append(material)

        objectTextu.select_set(True)
        bpy.ops.object.parent_set(type='OBJECT', xmirror=False, keep_transform=True)

        context.scene.cursor.location = zalohaCursoru
        context.scene.cursor.rotation_euler = zalohaRotaceCusoru

        return [objectKoty,objectTextu]
    
    def osadKotuArrowOpen(self, listKotaText, listVeci) -> bpy.types.Object:

        context = bpy.context

        zalohaCursoru = context.scene.cursor.location.copy()

        for porad in range(3):
            context.scene.cursor.location[porad] = 0

        objectKoty = listKotaText[0]

        self.ObjektKoty = objectKoty

        kotaBaseVert1 = listVeci[0]
        kotaBaseVert2 = listVeci[1]
        
        objectMesh = objectKoty.data
        pocetVert = 0

        if len(listVeci) > 2:
            self.odsazeniZakladna = self.zalohaOdsazeniZakladna
            self.odsazeniHlavni = listVeci[2]
            self.zalohaOdsazeniZakladna = self.odsazeniZakladna
            self.odsazeniZakladna = self.odsazeniZakladna + listVeci[3]

        #ziskame stred koty a posuneme object koty na tyto souradnice
        stredKoty = self.vratBodMeziDvemaBody(kotaBaseVert1, kotaBaseVert2) #stred koty uvnitr objektu
        for porad in range(3):
            objectKoty.location[porad] = stredKoty[porad]
        
        #nastavime rotaci koty podle vektoru
        self.rotaceDvaBody(objectKoty, kotaBaseVert1, kotaBaseVert2)

        #prepocitame vychozi body z world na local posunute a natocene koty
        kotaBaseVert1WorldBackUp = kotaBaseVert1
        kotaBaseVert2WorldBackUp = kotaBaseVert2
        bpy.context.view_layer.update()
        world_matrix_inv = objectKoty.matrix_world.inverted()
        kotaBaseVert1 = world_matrix_inv @ mathutils.Vector((kotaBaseVert1WorldBackUp[0], kotaBaseVert1WorldBackUp[1], kotaBaseVert1WorldBackUp[2]))
        kotaBaseVert2 = world_matrix_inv @ mathutils.Vector((kotaBaseVert2WorldBackUp[0], kotaBaseVert2WorldBackUp[1], kotaBaseVert2WorldBackUp[2]))

        kotaBaseVert1Original = kotaBaseVert1
        kotaBaseVert2Original = kotaBaseVert2

        #prvni body koty - vpravo
        kotaBaseVert1 = self.pripoctiY(kotaBaseVert1, self.odsazeniHlavni) #odsazujeme prvni body od zakladny dle jednotky, osa 2 je svisla nulova... to se musi doplnit jestli chceme podporu boku nejak... 
        objectMesh.vertices[pocetVert].co = kotaBaseVert1
        kotaBaseVert2 = self.pripoctiY(kotaBaseVert2, self.odsazeniHlavni)
        pocetVert += 1
        objectMesh.vertices[pocetVert].co = kotaBaseVert2

        #body prodlouzeni
        pocetVert += 1
        kotaBaseVert1prodl = self.pripoctiX(objectMesh.vertices[0].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = kotaBaseVert1prodl
        pocetVert += 1
        kotaBaseVert2prodl = self.pripoctiX(objectMesh.vertices[1].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = kotaBaseVert2prodl

        #pridam body vlevo a vpravo dle poloviny tloustka 4 + 4 a 4 + 4
        #4 kolem hlavni vpravo
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[0].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1 = self.pripoctiY(objectMesh.vertices[pocetVert].co, self.tloustka/2)
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[0].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1 = self.pripoctiY(objectMesh.vertices[pocetVert].co, -self.tloustka/2)
        objectMesh.vertices[pocetVert].co = bodSirky1

        #4 kolem hlavni vlevo
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[1].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1 = self.pripoctiY(objectMesh.vertices[pocetVert].co, self.tloustka/2)
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiY(objectMesh.vertices[pocetVert - 1].co, -self.tloustka)
        objectMesh.vertices[pocetVert].co = bodSirky1

        #spodni vpravo - stred,vlevo,vpravo
        pocetVert += 1
        kotaKolmiceSpodek1 = self.pripoctiY(kotaBaseVert1Original, self.odsazeniZakladna)
        objectMesh.vertices[pocetVert].co = kotaKolmiceSpodek1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 1].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 2].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1

        #spodni vlevo - stred,vlevo,vpravo
        pocetVert += 1
        kotaKolmiceSpodek2 = self.pripoctiY(kotaBaseVert2Original, self.odsazeniZakladna)
        objectMesh.vertices[pocetVert].co = kotaKolmiceSpodek2

        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 1].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 2].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1

        #horni vpravo - stred,vlevo,vpravo
        pocetVert += 1
        kotaKolmiceVrsek1 = self.pripoctiY(objectMesh.vertices[0].co, self.presahKolmice)
        objectMesh.vertices[pocetVert].co = kotaKolmiceVrsek1

        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 1].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 2].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1

        #horni vlevo - stred,vlevo,vpravo
        pocetVert += 1
        kotaKolmiceVrsek2 = self.pripoctiY(objectMesh.vertices[1].co, self.presahKolmice)
        objectMesh.vertices[pocetVert].co = kotaKolmiceVrsek2

        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 1].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 2].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vpravo horni 
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[4].co,math.sin(45/(180/math.pi))*(self.delkaSikmeCar/2))
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1=self.pripoctiX(objectMesh.vertices[pocetVert].co,-math.sin(45/(180/math.pi))*(self.delkaSikmeCar/2))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vpravo spodni
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[5].co,-math.sin(45/(180/math.pi))*(self.delkaSikmeCar/2))
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1=self.pripoctiX(objectMesh.vertices[pocetVert].co,-math.sin(45/(180/math.pi))*(self.delkaSikmeCar/2))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vpravo horni stred odsazeni
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[20].co,(-self.tloustka)*math.sin(45/(180/math.pi)))
        bodSirky1=self.pripoctiX(bodSirky1,-math.sin(45/(180/math.pi))*(self.tloustka))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vpravo spodni stred odsazeni
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[21].co,(self.tloustka)*math.sin(45/(180/math.pi)))
        bodSirky1=self.pripoctiX(bodSirky1,-math.sin(45/(180/math.pi))*(self.tloustka))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #horni diagonala pro diagonalu
        pocetVert +=1   
        bodSirky1=self.pripoctiX(objectMesh.vertices[4].co,-(self.tloustka)/math.sin(45/(180/math.pi)))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #spodni diagonala pro diagonalu - obe
        pocetVert +=1
        bodSirky1=self.pripoctiX(objectMesh.vertices[5].co,-(self.tloustka)/math.sin(45/(180/math.pi)))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vlevo horni stred
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[6].co,math.sin(45/(180/math.pi))*(self.delkaSikmeCar/2))
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1=self.pripoctiX(objectMesh.vertices[pocetVert].co,math.sin(45/(180/math.pi))*(self.delkaSikmeCar/2))
        objectMesh.vertices[pocetVert].co = bodSirky1
        #sikmina vlevo spodni stred
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[7].co,-math.sin(45/(180/math.pi))*(self.delkaSikmeCar/2))
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1=self.pripoctiX(objectMesh.vertices[pocetVert].co,math.sin(45/(180/math.pi))*(self.delkaSikmeCar/2))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vlevo horni stred odsazeni
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[26].co,(-self.tloustka)*math.sin(45/(180/math.pi)))
        bodSirky1=self.pripoctiX(bodSirky1,math.sin(45/(180/math.pi))*(self.tloustka))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vlevo spodni stred odsazeni
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[27].co,(self.tloustka)*math.sin(45/(180/math.pi)))
        bodSirky1=self.pripoctiX(bodSirky1,math.sin(45/(180/math.pi))*(self.tloustka))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #horni diagonala pro diagonalu 
        pocetVert +=1
        bodSirky1=self.pripoctiX(objectMesh.vertices[6].co,(self.tloustka)/math.sin(45/(180/math.pi)))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #spodni diagonala pro diagonalu
        pocetVert +=1   
        bodSirky1=self.pripoctiX(objectMesh.vertices[7].co,(self.tloustka)/math.sin(45/(180/math.pi)))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #orig snap points
        pocetVert +=1   
        bodSirky1=kotaBaseVert1Original
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert +=1   
        bodSirky1=kotaBaseVert2Original
        objectMesh.vertices[pocetVert].co = bodSirky1

        #hodime text do objektu
        objectTextu = listKotaText[1]
        self.ObjektTextu = objectTextu

        #ted vlastne pricteme location
        stredKotyOdsaz = self.vratBodMeziDvemaBody(kotaBaseVert1, kotaBaseVert2)
        for porad in range(3):
            objectTextu.location[porad] = stredKotyOdsaz[porad]
            
        #nastavime rotaci koty podle vektoru
        self.rotaceDvaBody(objectTextu, kotaBaseVert1, kotaBaseVert2)

        KotaNumber = self.vzdalenostMeziDvemaBody(kotaBaseVert1,kotaBaseVert2)
        KotaNumber = KotaNumber * self.distanceScale
        #tady uz bych to mohl oddelit podle ft in a metric
        if context.scene.DIMENSION.jednotky == 'ft in':
            textKoty = self.makeImperial(context, KotaNumber)
        elif context.scene.DIMENSION.jednotky == 'inches':
            textKoty = self.makeInches(context, KotaNumber)
        else:
            textKoty = str(round(KotaNumber, self.pocetDesetMist))
            textKoty = self.zaokrouhlNa(textKoty, self.pocetDesetMist)
            textKoty = self.vymenTeckuZaCarku(textKoty)
            textJednotek = context.scene.DIMENSION.jednotky
            if context.scene.DIMENSION.jednotky != 'None' and context.scene.DIMENSION.showUnits == True:
                textKoty = textKoty + ' ' + textJednotek

        #print(textKoty)
        objectTextu.data.body = textKoty
        objectTextu.data.align_x = 'CENTER'
        objectTextu.data.align_y = 'BOTTOM'
        objectTextu.data.offset_y = self.textOffset
        objectTextu.data.offset_x = self.textOffsetHor
        objectTextu.data.size = self.textSize

        #no a ted uz muzeme tocit na x
        objectTextu.rotation_euler.rotate_axis("Z", math.radians(self.textRotace))

        if math.isclose(objectTextu.rotation_euler[2], objectKoty.rotation_euler[2], abs_tol=0.001) == False: #tohle jenom dorovnava 360 stupnu na Z v pripadech kdy je to otocene o celych 360
            objectTextu.rotation_euler[2] = objectTextu.rotation_euler[2] + 2*math.pi
        
        objectKoty.rotation_euler[0] = math.radians(self.rotace)

        objectTextu.select_set(False)
        objectKoty.select_set(False)

        context.scene.cursor.location = zalohaCursoru

        return objectKoty
    
    def vytvorKotuSlopeNo(self) -> bpy.types.Object:

        context = bpy.context

        zalohaCursoru = context.scene.cursor.location.copy()
        zalohaRotaceCusoru = context.scene.cursor.rotation_euler.copy()

        #vytvorime novy objekt
        for porad in range(3):
            context.scene.cursor.location[porad] = 0
            context.scene.cursor.rotation_euler[porad] = 0

        #prihodime text
        bpy.ops.object.text_add()
        objectTextu = context.active_object
        self.ObjektTextu = objectTextu
        objectTextu.data.font = bpy.data.fonts[context.scene.DIMENSION.fontsArray]

        #bpy.ops.mesh.primitive_vert_add()
        bpy.ops.mesh.primitive_plane_add()

        objectKoty = context.active_object
        self.ObjektKoty = objectKoty
        objNameBase = 'dimension.'
        objName = 'dimension'
        counter = 1
        boolZapsano = False
        while boolZapsano == False:
            if bpy.data.objects.get(objName):
                #jmeno zabrano, pridavame + 1
                objName = objNameBase + str(counter)
                counter = counter + 1
            else:
                context.active_object.name = objName
                boolZapsano = True

        objectMesh = context.active_object.data
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.delete(type='EDGE_FACE') #pridana plane ma vsechno selected
        bpy.ops.object.mode_set(mode='OBJECT')

        objectMesh.vertices.add(40)

        for vert in objectMesh.vertices:
            vert.select = False

        bFA=bmesh.new()   
        bFA.from_mesh(objectMesh)
        bFA.verts.ensure_lookup_table()
        listVert = [bFA.verts[1],bFA.verts[0],bFA.verts[4],bFA.verts[8]] 
        vertsSequence = [bFA.verts[0],bFA.verts[1],bFA.verts[9],bFA.verts[6]] 
        #bmesh.ops.contextual_create(bFA, geom=listVert)
        bFA.faces.new(vertsSequence)
        bFA.faces.new(listVert)
        listVert = [bFA.verts[0],bFA.verts[6],bFA.verts[13],bFA.verts[12]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[0],bFA.verts[12],bFA.verts[14],bFA.verts[2]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[0],bFA.verts[2],bFA.verts[20],bFA.verts[18]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[0],bFA.verts[18],bFA.verts[19],bFA.verts[4]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[5],bFA.verts[7],bFA.verts[26],bFA.verts[24]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[5],bFA.verts[24],bFA.verts[27],bFA.verts[30]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[6],bFA.verts[25],bFA.verts[28],bFA.verts[32]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[6],bFA.verts[31],bFA.verts[29],bFA.verts[25]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[8],bFA.verts[39],bFA.verts[35],bFA.verts[33]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[8],bFA.verts[33],bFA.verts[36],bFA.verts[40]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[1],bFA.verts[8],bFA.verts[23],bFA.verts[21]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[1],bFA.verts[21],bFA.verts[22],bFA.verts[3]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[10],bFA.verts[11],bFA.verts[38],bFA.verts[34]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[10],bFA.verts[34],bFA.verts[37],bFA.verts[41]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[1],bFA.verts[3],bFA.verts[16],bFA.verts[15]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[1],bFA.verts[15],bFA.verts[17],bFA.verts[9]]
        bFA.faces.new(listVert)

        bFA.to_mesh(objectMesh)
        bFA.free()  

        #pridame material
        #testuju jestli material existuje
        material = None
        matNoneB = True
        for mat in bpy.data.materials:
            if mat.name == 'ColorBaseMat':
                material = mat
                matNoneB = False
                break
        if matNoneB == True:
            material = bpy.data.materials.new('ColorBaseMat')
            material.use_nodes = True
            material.node_tree.nodes.remove(material.node_tree.nodes["Principled BSDF"])
            emNode = material.node_tree.nodes.new('ShaderNodeEmission')
            emNode.inputs[0].default_value = 0,0,0,1
            material.node_tree.links.new(emNode.outputs[0],material.node_tree.nodes[0].inputs[0])

        objectKoty.data.materials.append(material)
        objectTextu.data.materials.append(material)

        objectTextu.select_set(True)
        bpy.ops.object.parent_set(type='OBJECT', xmirror=False, keep_transform=True)

        context.scene.cursor.location = zalohaCursoru
        context.scene.cursor.rotation_euler = zalohaRotaceCusoru

        return [objectKoty,objectTextu]
    
    def osadKotuSlopeNo(self, listKotaText, listVeci) -> bpy.types.Object:

        context = bpy.context

        zalohaCursoru = context.scene.cursor.location.copy()

        for porad in range(3):
            context.scene.cursor.location[porad] = 0

        objectKoty = listKotaText[0]

        self.ObjektKoty = objectKoty

        kotaBaseVert1 = listVeci[0]
        kotaBaseVert2 = listVeci[1]
        
        objectMesh = objectKoty.data
        pocetVert = 0

        if len(listVeci) > 2:
            self.odsazeniZakladna = self.zalohaOdsazeniZakladna
            self.odsazeniHlavni = listVeci[2]
            self.zalohaOdsazeniZakladna = self.odsazeniZakladna
            self.odsazeniZakladna = self.odsazeniZakladna + listVeci[3]
        
        #ziskame stred koty a posuneme object koty na tyto souradnice
        stredKoty = self.vratBodMeziDvemaBody(kotaBaseVert1, kotaBaseVert2) #stred koty uvnitr objektu
        for porad in range(3):
            objectKoty.location[porad] = stredKoty[porad]
        
        #nastavime rotaci koty podle vektoru
        self.rotaceDvaBody(objectKoty, kotaBaseVert1, kotaBaseVert2)

        #prepocitame vychozi body z world na local posunute a natocene koty
        kotaBaseVert1WorldBackUp = kotaBaseVert1
        kotaBaseVert2WorldBackUp = kotaBaseVert2
        bpy.context.view_layer.update()
        world_matrix_inv = objectKoty.matrix_world.inverted()
        kotaBaseVert1 = world_matrix_inv @ mathutils.Vector((kotaBaseVert1WorldBackUp[0], kotaBaseVert1WorldBackUp[1], kotaBaseVert1WorldBackUp[2]))
        kotaBaseVert2 = world_matrix_inv @ mathutils.Vector((kotaBaseVert2WorldBackUp[0], kotaBaseVert2WorldBackUp[1], kotaBaseVert2WorldBackUp[2]))

        kotaBaseVert1Original = kotaBaseVert1
        kotaBaseVert2Original = kotaBaseVert2

        #prvni body koty - vpravo
        kotaBaseVert1 = self.pripoctiY(kotaBaseVert1, self.odsazeniHlavni) #odsazujeme prvni body od zakladny dle jednotky, osa 2 je svisla nulova... to se musi doplnit jestli chceme podporu boku nejak... 
        objectMesh.vertices[pocetVert].co = kotaBaseVert1
        kotaBaseVert1Poradi = pocetVert
        kotaBaseVert2 = self.pripoctiY(kotaBaseVert2, self.odsazeniHlavni)
        pocetVert += 1
        objectMesh.vertices[pocetVert].co = kotaBaseVert2
        kotaBaseVert2Poradi = pocetVert
        #body prodlouzeni
        pocetVert += 1
        kotaBaseVert1prodl = self.pripoctiX(kotaBaseVert1, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = kotaBaseVert1prodl
        pocetVert += 1
        kotaBaseVert2prodl = self.pripoctiX(kotaBaseVert2, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = kotaBaseVert2prodl
        #pridam body vlevo a vpravo dle poloviny tloustka 4 + 4 a 4 + 4
        #4 kolem hlavni vpravo
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[kotaBaseVert1Poradi].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1 = self.pripoctiY(objectMesh.vertices[pocetVert].co, self.tloustka/2)
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[kotaBaseVert1Poradi].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1 = self.pripoctiY(objectMesh.vertices[pocetVert].co, self.tloustka/2)
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[kotaBaseVert1Poradi].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1 = self.pripoctiY(objectMesh.vertices[pocetVert].co, -self.tloustka/2)
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiY(objectMesh.vertices[pocetVert - 2].co, (-self.tloustka/2)/math.sin(45/(180/math.pi))) #(-self.tloustka/2)/math.sin(45/(180/math.pi))
        objectMesh.vertices[pocetVert].co = bodSirky1
        #4 kolem hlavni vlevo
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[kotaBaseVert2Poradi].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1 = self.pripoctiY(objectMesh.vertices[pocetVert].co, self.tloustka/2)
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiY(objectMesh.vertices[pocetVert - 1].co, -self.tloustka)
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 1].co, -self.tloustka)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiY(objectMesh.vertices[pocetVert - 1].co, (self.tloustka/2)/math.sin(45/(180/math.pi)))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #spodni vpravo - stred,vlevo,vpravo
        pocetVert += 1
        kotaKolmiceSpodek1 = self.pripoctiY(kotaBaseVert1Original, self.odsazeniZakladna)
        objectMesh.vertices[pocetVert].co = kotaKolmiceSpodek1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 1].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 2].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1

        #spodni vlevo - stred,vlevo,vpravo
        pocetVert += 1
        kotaKolmiceSpodek2 = self.pripoctiY(kotaBaseVert2Original, self.odsazeniZakladna)
        objectMesh.vertices[pocetVert].co = kotaKolmiceSpodek2
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 1].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 2].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1

        #horni vpravo - stred,vlevo,vpravo
        pocetVert += 1
        kotaKolmiceVrsek1 = self.pripoctiY(kotaBaseVert1, self.presahKolmice)
        objectMesh.vertices[pocetVert].co = kotaKolmiceVrsek1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 1].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 2].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1

        #horni vlevo - stred,vlevo,vpravo
        pocetVert += 1
        kotaKolmiceVrsek2 = self.pripoctiY(kotaBaseVert2, self.presahKolmice)
        objectMesh.vertices[pocetVert].co = kotaKolmiceVrsek2
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 1].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 2].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vpravo horni stred
        pocetVert +=1
        bodSirky1=self.pripoctiY(kotaBaseVert1,math.sin(45/(180/math.pi))*(self.delkaSikmeCar/2))
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1=self.pripoctiX(objectMesh.vertices[pocetVert].co,math.sin(45/(180/math.pi))*(self.delkaSikmeCar/2))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vpravo spodni stred
        pocetVert +=1
        bodSirky1=self.pripoctiY(kotaBaseVert1,-math.sin(45/(180/math.pi))*(self.delkaSikmeCar/2))
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1=self.pripoctiX(objectMesh.vertices[pocetVert].co,-math.sin(45/(180/math.pi))*(self.delkaSikmeCar/2))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vpravo horni stred odsazeni
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[pocetVert-2].co,(-self.tloustka/2)*math.sin(45/(180/math.pi)))
        bodSirky1=self.pripoctiX(bodSirky1,-math.sin(45/(180/math.pi))*(-self.tloustka/2))
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[pocetVert-3].co,(self.tloustka/2)*math.sin(45/(180/math.pi)))
        bodSirky1=self.pripoctiX(bodSirky1,-math.sin(45/(180/math.pi))*(self.tloustka/2))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vpravo spodni stred odsazeni
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[pocetVert-3].co,(-self.tloustka/2)*math.sin(45/(180/math.pi)))
        bodSirky1=self.pripoctiX(bodSirky1,-math.sin(45/(180/math.pi))*(-self.tloustka/2))
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[pocetVert-4].co,(self.tloustka/2)*math.sin(45/(180/math.pi)))
        bodSirky1=self.pripoctiX(bodSirky1,-math.sin(45/(180/math.pi))*(self.tloustka/2))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #horni diagonala pro diagonalu
        pocetVert +=1   
        bodSirky1=self.pripoctiY(objectMesh.vertices[5].co,(self.tloustka/2)/math.sin(45/(180/math.pi)))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #spodni diagonala pro diagonalu - obe
        pocetVert +=1
        bodSirky1=self.pripoctiX(objectMesh.vertices[6].co,-(self.tloustka/2)/math.sin(45/(180/math.pi)))
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert +=1   
        bodSirky1=self.pripoctiY(objectMesh.vertices[6].co,(-self.tloustka/2)/math.sin(45/(180/math.pi)))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vlevo horni stred
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[1].co,math.sin(45/(180/math.pi))*(self.delkaSikmeCar/2))
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1=self.pripoctiX(objectMesh.vertices[pocetVert].co,math.sin(45/(180/math.pi))*(self.delkaSikmeCar/2))
        objectMesh.vertices[pocetVert].co = bodSirky1
        #sikmina vlevo spodni stred
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[1].co,-math.sin(45/(180/math.pi))*(self.delkaSikmeCar/2))
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1=self.pripoctiX(objectMesh.vertices[pocetVert].co,-math.sin(45/(180/math.pi))*(self.delkaSikmeCar/2))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vlevo horni stred odsazeni
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[pocetVert-2].co,(-self.tloustka/2)*math.sin(45/(180/math.pi)))
        bodSirky1=self.pripoctiX(bodSirky1,math.sin(45/(180/math.pi))*(self.tloustka/2))
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[pocetVert-3].co,(self.tloustka/2)*math.sin(45/(180/math.pi)))
        bodSirky1=self.pripoctiX(bodSirky1,-math.sin(45/(180/math.pi))*(self.tloustka/2))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vlevo spodni stred odsazeni
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[pocetVert-3].co,(-self.tloustka/2)*math.sin(45/(180/math.pi)))
        bodSirky1=self.pripoctiX(bodSirky1,math.sin(45/(180/math.pi))*(self.tloustka/2))
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[pocetVert-4].co,(self.tloustka/2)*math.sin(45/(180/math.pi)))
        bodSirky1=self.pripoctiX(bodSirky1,-math.sin(45/(180/math.pi))*(self.tloustka/2))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #horni diagonala pro diagonalu - obe
        pocetVert +=1
        bodSirky1=self.pripoctiX(objectMesh.vertices[8].co,(self.tloustka/2)/math.sin(45/(180/math.pi)))
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert +=1   
        bodSirky1=self.pripoctiY(objectMesh.vertices[8].co,(self.tloustka/2)/math.sin(45/(180/math.pi)))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #spodni diagonala pro diagonalu
        pocetVert +=1   
        bodSirky1=self.pripoctiY(objectMesh.vertices[10].co,(-self.tloustka/2)/math.sin(45/(180/math.pi)))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #orig snap points
        pocetVert +=1   
        bodSirky1=kotaBaseVert1Original
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert +=1   
        bodSirky1=kotaBaseVert2Original
        objectMesh.vertices[pocetVert].co = bodSirky1

        #hodime text do objektu
        objectTextu = listKotaText[1]
        self.ObjektTextu = objectTextu

        #ted vlastne pricteme location
        stredKotyOdsaz = self.vratBodMeziDvemaBody(kotaBaseVert1, kotaBaseVert2)
        for porad in range(3):
            objectTextu.location[porad] = stredKotyOdsaz[porad]
            
        #nastavime rotaci koty podle vektoru
        self.rotaceDvaBody(objectTextu, kotaBaseVert1, kotaBaseVert2)

        KotaNumber = self.vzdalenostMeziDvemaBody(kotaBaseVert1,kotaBaseVert2)
        KotaNumber = KotaNumber * self.distanceScale
        #tady uz bych to mohl oddelit podle ft in a metric
        if context.scene.DIMENSION.jednotky == 'ft in':
            textKoty = self.makeImperial(context, KotaNumber)
        elif context.scene.DIMENSION.jednotky == 'inches':
            textKoty = self.makeInches(context, KotaNumber)
        else:
            textKoty = str(round(KotaNumber, self.pocetDesetMist))
            textKoty = self.zaokrouhlNa(textKoty, self.pocetDesetMist)
            textKoty = self.vymenTeckuZaCarku(textKoty)
            textJednotek = context.scene.DIMENSION.jednotky
            if context.scene.DIMENSION.jednotky != 'None' and context.scene.DIMENSION.showUnits == True:
                textKoty = textKoty + ' ' + textJednotek

        #print(textKoty)
        objectTextu.data.body = textKoty
        objectTextu.data.align_x = 'CENTER'
        objectTextu.data.align_y = 'BOTTOM'
        objectTextu.data.offset_y = self.textOffset
        objectTextu.data.offset_x = self.textOffsetHor
        objectTextu.data.size = self.textSize
        
        #no a ted uz muzeme tocit na x
        objectTextu.rotation_euler.rotate_axis("Z", math.radians(self.textRotace))

        if math.isclose(objectTextu.rotation_euler[2], objectKoty.rotation_euler[2], abs_tol=0.001) == False: #tohle jenom dorovnava 360 stupnu na Z v pripadech kdy je to otocene o celych 360
            objectTextu.rotation_euler[2] = objectTextu.rotation_euler[2] + 2*math.pi

        objectKoty.rotation_euler[0] = math.radians(self.rotace)

        objectTextu.select_set(False)
        objectKoty.select_set(False)

        context.scene.cursor.location = zalohaCursoru

        return
    
    def vytvorKotuSlope(self) -> bpy.types.Object:

        context = bpy.context

        zalohaCursoru = context.scene.cursor.location.copy()
        zalohaRotaceCusoru = context.scene.cursor.rotation_euler.copy()

        #vytvorime novy objekt
        for porad in range(3):
            context.scene.cursor.location[porad] = 0
            context.scene.cursor.rotation_euler[porad] = 0

        #prihodime text
        bpy.ops.object.text_add()
        objectTextu = context.active_object
        self.ObjektTextu = objectTextu
        objectTextu.data.font = bpy.data.fonts[context.scene.DIMENSION.fontsArray]

        #bpy.ops.mesh.primitive_vert_add()
        bpy.ops.mesh.primitive_plane_add()

        objectKoty = context.active_object
        self.ObjektKoty = objectKoty
        objNameBase = 'dimension.'
        objName = 'dimension'
        counter = 1
        boolZapsano = False
        while boolZapsano == False:
            if bpy.data.objects.get(objName):
                #jmeno zabrano, pridavame + 1
                objName = objNameBase + str(counter)
                counter = counter + 1
            else:
                context.active_object.name = objName
                boolZapsano = True

        objectMesh = context.active_object.data
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.delete(type='EDGE_FACE') #pridana plane ma vsechno selected
        bpy.ops.object.mode_set(mode='OBJECT')

        objectMesh.vertices.add(46)

        for vert in objectMesh.vertices:
            vert.select = False
            
        #pridame mesh
        #bmesh.ops.contextual_create(bm, geom=[], mat_nr=0, use_smooth=False)
        bFA=bmesh.new()   
        bFA.from_mesh(objectMesh)
        bFA.verts.ensure_lookup_table()
        listVert = [bFA.verts[1],bFA.verts[0],bFA.verts[4],bFA.verts[9]] 
        vertsSequence = [bFA.verts[0],bFA.verts[1],bFA.verts[11],bFA.verts[6]] 
        #bmesh.ops.contextual_create(bFA, geom=listVert)
        bFA.faces.new(vertsSequence)
        bFA.faces.new(listVert)
        listVert = [bFA.verts[0],bFA.verts[6],bFA.verts[17],bFA.verts[16]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[0],bFA.verts[16],bFA.verts[18],bFA.verts[7]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[0],bFA.verts[7],bFA.verts[15],bFA.verts[2]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[0],bFA.verts[2],bFA.verts[14],bFA.verts[5]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[0],bFA.verts[5],bFA.verts[24],bFA.verts[22]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[0],bFA.verts[22],bFA.verts[23],bFA.verts[4]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[1],bFA.verts[9],bFA.verts[27],bFA.verts[25]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[1],bFA.verts[25],bFA.verts[26],bFA.verts[8]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[1],bFA.verts[8],bFA.verts[12],bFA.verts[3]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[1],bFA.verts[3],bFA.verts[13],bFA.verts[10]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[1],bFA.verts[10],bFA.verts[20],bFA.verts[19]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[1],bFA.verts[19],bFA.verts[21],bFA.verts[11]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[5],bFA.verts[34],bFA.verts[30],bFA.verts[28]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[5],bFA.verts[28],bFA.verts[31],bFA.verts[35]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[6],bFA.verts[29],bFA.verts[32],bFA.verts[37]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[6],bFA.verts[36],bFA.verts[33],bFA.verts[29]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[9],bFA.verts[44],bFA.verts[40],bFA.verts[38]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[9],bFA.verts[38],bFA.verts[41],bFA.verts[45]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[10],bFA.verts[39],bFA.verts[42],bFA.verts[47]]
        bFA.faces.new(listVert)
        listVert = [bFA.verts[10],bFA.verts[46],bFA.verts[43],bFA.verts[39]]
        bFA.faces.new(listVert)

        bFA.to_mesh(objectMesh)
        bFA.free()  

        #pridame material
        #testuju jestli material existuje
        material = None
        matNoneB = True
        for mat in bpy.data.materials:
            if mat.name == 'ColorBaseMat':
                material = mat
                matNoneB = False
                break
        if matNoneB == True:
            material = bpy.data.materials.new('ColorBaseMat')
            material.use_nodes = True
            material.node_tree.nodes.remove(material.node_tree.nodes["Principled BSDF"])
            emNode = material.node_tree.nodes.new('ShaderNodeEmission')
            emNode.inputs[0].default_value = 0,0,0,1
            material.node_tree.links.new(emNode.outputs[0],material.node_tree.nodes[0].inputs[0])

        objectKoty.data.materials.append(material)
        objectTextu.data.materials.append(material)

        #context.view_layer.objects.active = objectKoty
        objectTextu.select_set(True)
        bpy.ops.object.parent_set(type='OBJECT', xmirror=False, keep_transform=True)

        context.scene.cursor.location = zalohaCursoru
        context.scene.cursor.rotation_euler = zalohaRotaceCusoru

        return [objectKoty,objectTextu]
    
    def osadKotuSlope(self, listKotaText, listVeci):
        context = bpy.context

        zalohaCursoru = context.scene.cursor.location.copy()
        
        for porad in range(3):
            context.scene.cursor.location[porad] = 0

        objectKoty = listKotaText[0]

        self.ObjektKoty = objectKoty

        kotaBaseVert1 = listVeci[0]
        kotaBaseVert2 = listVeci[1]
        
        objectMesh = objectKoty.data
        pocetVert = 0

        #prepsat eventuelne odsazeni - pridat neco aby to odsazeniHlavni provadelo jenom pri prekroceni urcite meze - asi neni treba
        if len(listVeci) > 2:
            self.odsazeniZakladna = self.zalohaOdsazeniZakladna
            self.odsazeniHlavni = listVeci[2]
            self.zalohaOdsazeniZakladna = self.odsazeniZakladna
            self.odsazeniZakladna = self.odsazeniZakladna + listVeci[3]

        #ziskame stred koty a posuneme object koty na tyto souradnice
        stredKoty = self.vratBodMeziDvemaBody(kotaBaseVert1, kotaBaseVert2) #stred koty uvnitr objektu
        for porad in range(3):
            objectKoty.location[porad] = stredKoty[porad]
        
        #nastavime rotaci koty podle vektoru
        self.rotaceDvaBody(objectKoty, kotaBaseVert1, kotaBaseVert2)

        #prepocitame vychozi body z world na local posunute a natocene koty
        kotaBaseVert1WorldBackUp = kotaBaseVert1
        kotaBaseVert2WorldBackUp = kotaBaseVert2
        bpy.context.view_layer.update()
        world_matrix_inv = objectKoty.matrix_world.inverted()
        kotaBaseVert1 = world_matrix_inv @ mathutils.Vector((kotaBaseVert1WorldBackUp[0], kotaBaseVert1WorldBackUp[1], kotaBaseVert1WorldBackUp[2]))
        kotaBaseVert2 = world_matrix_inv @ mathutils.Vector((kotaBaseVert2WorldBackUp[0], kotaBaseVert2WorldBackUp[1], kotaBaseVert2WorldBackUp[2]))

        kotaBaseVert1Original = kotaBaseVert1
        kotaBaseVert2Original = kotaBaseVert2

        #prvni body koty - vpravo
        #kotaBaseVert1 = self.odsad(kotaBaseVert1, vektorSmer, 2, self.odsazeniHlavni)
        kotaBaseVert1 = self.pripoctiY(kotaBaseVert1, self.odsazeniHlavni) #Y je jakoby KOLMO
        objectMesh.vertices[pocetVert].co = kotaBaseVert1
        kotaBaseVert1Poradi = pocetVert

        #kotaBaseVert2 = self.odsad(kotaBaseVert2, vektorSmer, 2, self.odsazeniHlavni)
        kotaBaseVert2 = self.pripoctiY(kotaBaseVert2, self.odsazeniHlavni)
        pocetVert += 1
        objectMesh.vertices[pocetVert].co = kotaBaseVert2
        kotaBaseVert2Poradi = pocetVert

        #body prodlouzeni
        pocetVert += 1
        #kotaBaseVert1prodl = self.pripoctiNejOsa(kotaBaseVert1, vektorSmer, -self.protazeni)  
        kotaBaseVert1prodl = self.pripoctiX(kotaBaseVert1, self.protazeni)
        objectMesh.vertices[pocetVert].co = kotaBaseVert1prodl

        pocetVert += 1
        #kotaBaseVert2prodl = self.pripoctiNejOsa(kotaBaseVert2, vektorSmer, self.protazeni)  
        kotaBaseVert2prodl = self.pripoctiX(kotaBaseVert2, -self.protazeni)
        objectMesh.vertices[pocetVert].co = kotaBaseVert2prodl

        #pridam body vlevo a vpravo dle poloviny tloustka 4 + 4 a 4 + 4
        #4 kolem hlavni vpravo
        pocetVert += 1
        #bodSirky1 = self.pripoctiNejOsa(objectMesh.vertices[kotaBaseVert1Poradi].co, vektorSmer, self.tloustka/2)  
        bodSirky1 = self.pripoctiX(objectMesh.vertices[kotaBaseVert1Poradi].co, -self.tloustka/2)
        objectMesh.vertices[pocetVert].co = bodSirky1
        #bodSirky1 = self.odsad(objectMesh.vertices[pocetVert].co, vektorSmer, 2, self.tloustka/2)
        bodSirky1 = self.pripoctiY(objectMesh.vertices[pocetVert].co, self.tloustka/2)
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[kotaBaseVert1Poradi].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1 = self.pripoctiY(objectMesh.vertices[pocetVert].co, self.tloustka/2)
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[kotaBaseVert1Poradi].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1 = self.pripoctiY(objectMesh.vertices[pocetVert].co, -self.tloustka/2)
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[kotaBaseVert1Poradi].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1 = self.pripoctiY(objectMesh.vertices[pocetVert].co, -self.tloustka/2)
        objectMesh.vertices[pocetVert].co = bodSirky1
        #4 kolem hlavni vlevo
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[kotaBaseVert2Poradi].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1 = self.pripoctiY(objectMesh.vertices[pocetVert].co, self.tloustka/2)
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[kotaBaseVert2Poradi].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1 = self.pripoctiY(objectMesh.vertices[pocetVert].co, self.tloustka/2)
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[kotaBaseVert2Poradi].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1 = self.pripoctiY(objectMesh.vertices[pocetVert].co, -self.tloustka/2)
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[kotaBaseVert2Poradi].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1 = self.pripoctiY(objectMesh.vertices[pocetVert].co, -self.tloustka/2)
        objectMesh.vertices[pocetVert].co = bodSirky1
        #protazeni v hlavnim smeru vlevo a pak vpravo
        pocetVert += 1
        bodSirky1 = self.pripoctiY(objectMesh.vertices[3].co, self.tloustka/2)
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiY(objectMesh.vertices[3].co, -self.tloustka/2)
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiY(objectMesh.vertices[2].co, self.tloustka/2)
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiY(objectMesh.vertices[2].co, -self.tloustka/2)
        objectMesh.vertices[pocetVert].co = bodSirky1

        #spodni vpravo - stred,vlevo,vpravo
        pocetVert += 1
        kotaKolmiceSpodek1 = self.pripoctiY(kotaBaseVert1Original, self.odsazeniZakladna)
        objectMesh.vertices[pocetVert].co = kotaKolmiceSpodek1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 1].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 2].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        #spodni vlevo - stred,vlevo,vpravo
        pocetVert += 1
        kotaKolmiceSpodek2 = self.pripoctiY(kotaBaseVert2Original, self.odsazeniZakladna)
        objectMesh.vertices[pocetVert].co = kotaKolmiceSpodek2
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 1].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 2].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        #horni vpravo - stred,vlevo,vpravo
        pocetVert += 1
        kotaKolmiceVrsek1 = self.pripoctiY(kotaBaseVert1, self.presahKolmice)
        objectMesh.vertices[pocetVert].co = kotaKolmiceVrsek1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 1].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 2].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        #horni vlevo - stred,vlevo,vpravo
        pocetVert += 1
        kotaKolmiceVrsek2 = self.pripoctiY(kotaBaseVert2, self.presahKolmice)
        objectMesh.vertices[pocetVert].co = kotaKolmiceVrsek2
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 1].co, -self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert += 1
        bodSirky1 = self.pripoctiX(objectMesh.vertices[pocetVert - 2].co, self.tloustka/2)  
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vpravo horni stred
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[0].co,math.sin(45/(180/math.pi))*(self.delkaSikmeCar/2))
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1=self.pripoctiX(objectMesh.vertices[pocetVert].co,math.sin(45/(180/math.pi))*(self.delkaSikmeCar/2))
        objectMesh.vertices[pocetVert].co = bodSirky1
        #sikmina vpravo spodni stred
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[0].co,-math.sin(45/(180/math.pi))*(self.delkaSikmeCar/2))
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1=self.pripoctiX(objectMesh.vertices[pocetVert].co,-math.sin(45/(180/math.pi))*(self.delkaSikmeCar/2))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vpravo horni stred odsazeni
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[pocetVert-2].co,(-self.tloustka/2)*math.sin(45/(180/math.pi)))
        bodSirky1=self.pripoctiX(bodSirky1,math.sin(45/(180/math.pi))*(self.tloustka/2))
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[pocetVert-3].co,(self.tloustka/2)*math.sin(45/(180/math.pi)))
        bodSirky1=self.pripoctiX(bodSirky1,math.sin(45/(180/math.pi))*(-self.tloustka/2))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vpravo spodni stred odsazeni
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[pocetVert-3].co,(-self.tloustka/2)*math.sin(45/(180/math.pi)))
        bodSirky1=self.pripoctiX(bodSirky1,math.sin(45/(180/math.pi))*(self.tloustka/2))
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[pocetVert-4].co,(self.tloustka/2)*math.sin(45/(180/math.pi)))
        bodSirky1=self.pripoctiX(bodSirky1,math.sin(45/(180/math.pi))*(-self.tloustka/2))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #horni diagonala pro diagonalu - obe
        pocetVert +=1
        bodSirky1=self.pripoctiX(objectMesh.vertices[5].co,(self.tloustka/2)/math.sin(45/(180/math.pi)))
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert +=1   
        bodSirky1=self.pripoctiY(objectMesh.vertices[5].co,(self.tloustka/2)/math.sin(45/(180/math.pi)))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #spodni diagonala pro diagonalu - obe
        pocetVert +=1
        bodSirky1=self.pripoctiX(objectMesh.vertices[6].co,(-self.tloustka/2)/math.sin(45/(180/math.pi)))
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert +=1   
        bodSirky1=self.pripoctiY(objectMesh.vertices[6].co,(-self.tloustka/2)/math.sin(45/(180/math.pi)))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vlevo horni stred
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[1].co,math.sin(45/(180/math.pi))*(self.delkaSikmeCar/2))
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1=self.pripoctiX(objectMesh.vertices[pocetVert].co,math.sin(45/(180/math.pi))*(self.delkaSikmeCar/2))
        objectMesh.vertices[pocetVert].co = bodSirky1
        #sikmina vlevo spodni stred
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[1].co,-math.sin(45/(180/math.pi))*(self.delkaSikmeCar/2))
        objectMesh.vertices[pocetVert].co = bodSirky1
        bodSirky1=self.pripoctiX(objectMesh.vertices[pocetVert].co,-math.sin(45/(180/math.pi))*(self.delkaSikmeCar/2))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vlevo horni stred odsazeni
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[pocetVert-2].co,(-self.tloustka/2)*math.sin(45/(180/math.pi)))
        bodSirky1=self.pripoctiX(bodSirky1,math.sin(45/(180/math.pi))*(self.tloustka/2))
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[pocetVert-3].co,(self.tloustka/2)*math.sin(45/(180/math.pi)))
        bodSirky1=self.pripoctiX(bodSirky1,math.sin(45/(180/math.pi))*(-self.tloustka/2))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #sikmina vlevo spodni stred odsazeni
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[pocetVert-3].co,(-self.tloustka/2)*math.sin(45/(180/math.pi)))
        bodSirky1=self.pripoctiX(bodSirky1,math.sin(45/(180/math.pi))*(self.tloustka/2))
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert +=1
        bodSirky1=self.pripoctiY(objectMesh.vertices[pocetVert-4].co,(self.tloustka/2)*math.sin(45/(180/math.pi)))
        bodSirky1=self.pripoctiX(bodSirky1,math.sin(45/(180/math.pi))*(-self.tloustka/2))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #horni diagonala pro diagonalu - obe
        pocetVert +=1
        bodSirky1=self.pripoctiX(objectMesh.vertices[9].co,(self.tloustka/2)/math.sin(45/(180/math.pi)))
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert +=1   
        bodSirky1=self.pripoctiY(objectMesh.vertices[9].co,(self.tloustka/2)/math.sin(45/(180/math.pi)))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #spodni diagonala pro diagonalu - obe
        pocetVert +=1
        bodSirky1=self.pripoctiX(objectMesh.vertices[10].co,(-self.tloustka/2)/math.sin(45/(180/math.pi)))
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert +=1   
        bodSirky1=self.pripoctiY(objectMesh.vertices[10].co,(-self.tloustka/2)/math.sin(45/(180/math.pi)))
        objectMesh.vertices[pocetVert].co = bodSirky1

        #orig snap points
        pocetVert +=1   
        bodSirky1=kotaBaseVert1Original
        objectMesh.vertices[pocetVert].co = bodSirky1
        pocetVert +=1   
        bodSirky1=kotaBaseVert2Original
        objectMesh.vertices[pocetVert].co = bodSirky1

        #hodime text do objektu
        objectTextu = listKotaText[1]
        self.ObjektTextu = objectTextu

        #ted vlastne pricteme location
        stredKotyOdsaz = self.vratBodMeziDvemaBody(kotaBaseVert1, kotaBaseVert2)
        for porad in range(3):
            objectTextu.location[porad] = stredKotyOdsaz[porad]
            
        #nastavime rotaci koty podle vektoru
        self.rotaceDvaBody(objectTextu, kotaBaseVert1, kotaBaseVert2)

        KotaNumber = self.vzdalenostMeziDvemaBody(kotaBaseVert1,kotaBaseVert2)
        KotaNumber = KotaNumber * self.distanceScale
        #tady uz bych to mohl oddelit podle ft in a metric
        if context.scene.DIMENSION.jednotky == 'ft in':
            textKoty = self.makeImperial(context, KotaNumber)
        elif context.scene.DIMENSION.jednotky == 'inches':
            textKoty = self.makeInches(context, KotaNumber)
        else:
            textKoty = str(round(KotaNumber, self.pocetDesetMist))
            textKoty = self.zaokrouhlNa(textKoty, self.pocetDesetMist)
            textKoty = self.vymenTeckuZaCarku(textKoty)
            textJednotek = context.scene.DIMENSION.jednotky
            if context.scene.DIMENSION.jednotky != 'None' and context.scene.DIMENSION.showUnits == True:
                textKoty = textKoty + ' ' + textJednotek

        #print(textKoty)
        objectTextu.data.body = textKoty
        objectTextu.data.align_x = 'CENTER'
        objectTextu.data.align_y = 'BOTTOM'
        objectTextu.data.offset_y = self.textOffset
        objectTextu.data.offset_x = self.textOffsetHor
        objectTextu.data.size = self.textSize

        #objectTextu.select_set(False)
        objectTextu.rotation_euler.rotate_axis("Z", math.radians(self.textRotace))

        if math.isclose(objectTextu.rotation_euler[2], objectKoty.rotation_euler[2], abs_tol=0.001) == False: #tohle jenom dorovnava 360 stupnu na Z v pripadech kdy je to otocene o celych 360
            objectTextu.rotation_euler[2] = objectTextu.rotation_euler[2] + 2*math.pi

        #no a ted bych mel jeste otocit celou kotou dle globals?

        objectKoty.rotation_euler[0] = math.radians(self.rotace)

        objectTextu.select_set(False)
        objectKoty.select_set(False)
        #'''
        context.scene.cursor.location = zalohaCursoru

        return

    def pripoctiX(self, vektorBase: list[float], vzdalenost: float) -> list[float]:
        posunutyBod = [vektorBase[0] + vzdalenost,vektorBase[1],vektorBase[2]]
        return posunutyBod

    def pripoctiY(self, vektorBase: list[float], vzdalenost: float) -> list[float]:
        posunutyBod = [vektorBase[0],vektorBase[1] + vzdalenost,vektorBase[2]]
        return posunutyBod
    
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

    #objekt1 bude mit rotace jako objekt2 a stred mezi body 0 a 1 v listVeci
    def srovnejRotationEulerObjektum(self, objekt1, objekt2, listVeci):

        if self.debug == True:
            self.timeItStop = timer()
            print('START srovnejRotationEulerObjektum ' + str((self.timeItStop - self.timeItStart)*1000))

        context = bpy.context

        if self.debug == True:
            self.timeItStop = timer()
            print('BEFORE DESELECT ' + str((self.timeItStop - self.timeItStart)*1000))

        bpy.ops.object.select_all(action='DESELECT')

        if self.debug == True:
            self.timeItStop = timer()
            print('AFTER DESELECT ' + str((self.timeItStop - self.timeItStart)*1000))

        zalohaCursoru = context.scene.cursor.location.copy()
        
        #nastavime kote origin na stred origo bodu 
        stredKotyBB = self.vratBodMeziDvemaBody(listVeci[0], listVeci[1]) #stred koty uvnitr objektu
        for porad in range(3):
            context.scene.cursor.location[porad] = stredKotyBB[porad]

        #objekt2.select_set(False)
        #objekt1.select_set(False)
        
        context.view_layer.objects.active = objekt1
        objekt1.select_set(True)
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN') #mam cursor posunuty na stred mezi vychozi body a tam hodim i origin

        zalohaRotationEulerTextu = [0.0,0.0,0.0]
        for porad in range(3):
            zalohaRotationEulerTextu[porad] = objekt2.rotation_euler[porad]

        objekt2.rotation_euler.rotate_axis("Z", -math.radians(self.textRotace))

        #jako u textu spocitat uhly, otocit do nul, apply a otocit zpet - vlastne zkopiruju jenom uhly textu...
        rotaceList = [objekt2.rotation_euler[0]*-1,objekt2.rotation_euler[1]*-1, objekt2.rotation_euler[2]*-1]
        objekt1.rotation_mode = 'ZYX'
        objekt1.rotation_euler = (rotaceList)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False, properties=False, isolate_users=False)
        #for porad in range(3):
            #objekt2.rotation_euler[porad] = zalohaRotationEulerTextu[porad]

        rotaceList = [objekt2.rotation_euler[0],objekt2.rotation_euler[1], objekt2.rotation_euler[2]]
        objekt1.rotation_mode = 'XYZ' #set rotation mode back (was zyx, so we want xyz)
        objekt1.rotation_euler = (rotaceList) #set rotation

        objekt2.rotation_euler.rotate_axis("Z", math.radians(self.textRotace))


        context.view_layer.objects.active = objekt1
        objekt2.select_set(True)
        objekt1.select_set(True)

        if self.debug == True:
            self.timeItStop = timer()
            print('BEFORE PARENT_SET ' + str((self.timeItStop - self.timeItStart)*1000))

        bpy.ops.object.parent_set(type='OBJECT', xmirror=False, keep_transform=True)

        if self.debug == True:
            self.timeItStop = timer()
            print('AFTER PARENT_SET ' + str((self.timeItStop - self.timeItStart)*1000))

        #no a ted uz muzeme tocit na x
        objekt1.rotation_euler[0] = objekt1.rotation_euler[0] + math.radians(self.rotace)

        context.scene.cursor.location = zalohaCursoru

        if self.debug == True:
            self.timeItStop = timer()
            print('KONEC srovnejRotationEulerObjektum ' + str((self.timeItStop - self.timeItStart)*1000))

        return

    def vratBodMeziDvemaBody(self, bod1: list[float], bod2: list[float]) -> list[float]:
        vysledek = [0.0,0.0,0.0]
        vysledek[0] = (bod1[0] + bod2[0])/2
        vysledek[1] = (bod1[1] + bod2[1])/2
        vysledek[2] = (bod1[2] + bod2[2])/2
        return vysledek

    def vratPosledniEdge(self, meshObject) -> int:
        counter = 0
        for edges in meshObject.edges:
            counter += 1
        return counter

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

    def smerovyVektor(self, vektorBase: list[float], vektorSmer: list[float]) -> list[float]:
        sX = vektorSmer[0] - vektorBase[0]
        sY = vektorSmer[1] - vektorBase[1]
        sZ = vektorSmer[2] - vektorBase[2]
        vysledek = [sX, sY, sZ]
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
    
    def vymenCarkuZaTecku(self, text: str) -> str:
        vysledek = ''
        for i in text:
            if i == ',':
                vysledek = vysledek + '.'
            else:
                vysledek = vysledek + i
        return vysledek

    def addMaterial():
        object = None
        material = bpy.data.materials.new(name="Redish")
        material.use_nodes = True
        nodes = material.node_tree.nodes
        emissionNode = nodes.new(type='ShaderNodeEmission')
        emissionNode.inputs[0].default_value = (0.8,0.0,0.0,1)
        emissionNode.inputs[1].default_value = 1
        links = material.node_tree.links
        links.new(emissionNode.outputs[0],nodes['Material Output'].inputs[0])
        object.data.materials.append(material)

class SFA_OT_realtime_dimension(bpy.types.Operator): #opravit cursor movement
    """Realtime dimensions."""
    bl_idname='dimension.create'
    bl_label='Create dimensions.'

    debug = False

    #tady se pokusit pretahnou data z MESH_OT_dimension_edit
    protazeni: bpy.props.FloatProperty(name="extend",description="length of extension",default=1,min = 0,) # type: ignore
    odsazeniHlavni: bpy.props.FloatProperty(name="distance",description="distance of mine line",default=1.4,min = 0,) # type: ignore
    odsazeniZakladna: bpy.props.FloatProperty(name="distance from base",description="distance from base",default=0.4,min = 0,) # type: ignore
    presahKolmice: bpy.props.FloatProperty(name="distance above main line",description="distance above main line",default=0.6,min = 0,) # type: ignore
    otocit: bpy.props.BoolProperty(name="switch side",description="switch to other side",default = False,) # type: ignore
    pocetDesetMist: bpy.props.IntProperty(name="decimal places",description="number of decimal places",default = 3,min = 0,) # type: ignore
    textOffset: bpy.props.FloatProperty(name="text baseline distance",description="text distance from baseline",default = 0,) # type: ignore
    textOffsetHor: bpy.props.FloatProperty(name="text baseline center offset",description="text offset from baseline center",default = 0,) # type: ignore
    meritko: bpy.props.IntProperty(name="1 : ",description="dimension text scale",default = 1,) # type: ignore
    rotace: bpy.props.IntProperty(name="rotation",description="rotate dimension",default = 0, min = -180,max = 180,) # type: ignore
    textRotace: bpy.props.IntProperty(name="text rotation",description="rotate text",default = 0,min = -180,max = 180,) # type: ignore
    tloustka: bpy.props.FloatProperty(name="line width",description="line width",default=0.1,min = 0,) # type: ignore
    delkaSikmeCar: bpy.props.FloatProperty(name="border sign size", description="border sign size", default=1, min=0,) # type: ignore
    textSize: bpy.props.FloatProperty(name="text size",description="text size",default=1,min=0,) # type: ignore
    distanceScale: bpy.props.FloatProperty(name="distance scale",description="scale for distance calculation",default = 1,min = 0,) # type: ignore
    #listVertB: bpy.props.BoolProperty(name="listVertB",description="load UI help",default = False, options={'HIDDEN'})
    lockAxis: bpy.props.IntProperty(name='lockAxis',description="axis lock",default = 0,min = 0,max = 3, options={'HIDDEN'})#zkusime vynechat # type: ignore

    counter = 0
    lastLocation = [0,0,0]
    vyslednyVektor = mathutils.Vector((0.0, 0.0, 0.0))
    prvniBod = False
    objektFirsPoint = None
    zalohaCisla = mathutils.Vector((0.0, 0.0, 0.0))
    currentState = 0 #0, 1, 2
    prvniBodKotyCoord = mathutils.Vector((0.0, 0.0, 0.0))
    druhyBodKotyCoord = mathutils.Vector((0.0, 0.0, 0.0)) #pridat jeste vzdalenost a odsazeni...
    ObjektKoty = None
    ObjektTextu = None
    vektorFin = mathutils.Vector((0.0, 0.0, 0.0))
    jmenoObjektuKoty = ''
    final2Dregion = []
    posunKolecka = 0.0
    zalohaOdsazeniZakladna = 0.0
    listKotaText = []
    odsazZakl = 0.0
    wheelChange = False
    ObjektFaceRayCast = None
    nevimHandle = None
    nevimHandle2 = None
    mouseLocation = [0,0]
    snap2Dfin = [0,0]
    snap3Dfin = mathutils.Vector((0.0, 0.0, 0.0))
    textToDraw = ''
    delkaManual = ''
    delkaManualFloat = 0.0
    osazeno = False
    lockAxisX = False
    lockAxisY = False
    lockAxisZ = False
    middlePoint = False
    middlePointHelp = False
    timeStart = 0.0
    timeStop = 0.0
    timeItStart = 0.0
    timeItStop = 0.0
    binTreeInstance = None
    listStredu = []
    snapReset = True
    snapObjectsState = False
    snapVerticesState = False
    snapMiddlesState = False
    snapObjectsIterator = 0
    snapVerticeIterator = 0
    snapMiddlesIterator = 0
    snapFinished = False
    counterStredy = -1
    velikostStromu = 0
    mouseMoved = False
    ccc = 0
    continueMode = False
    continueModeText = 'OFF'
    continueModeHelpBool = False
    edgesMiddleText = 'turned off'

    def modal(self, context: bpy.types.Context, event: bpy.types.Event):
        #self.ccc += 1
        #print('NEW MODAL')
        #print(self.ccc)

        #print(event.type)
        #print(event.value)
        #print(context.space_data.region_3d.view_perspective)
        #print(context.space_data.region_3d)
        #print(context.region)
        #if context.space_data.region_3d.view_perspective == 'CAMERA':
            #context.space_data.region_3d.view_perspective = 'ORTHO'
            #pass
        context.area.tag_redraw()

        #pro mouseWheel
        if self.currentState == 2:
            if event.type == 'WHEELUPMOUSE':
                self.posunKolecka = self.posunKolecka + self.tloustka
                self.wheelChange = True
            if event.type == 'WHEELDOWNMOUSE':
                self.posunKolecka = self.posunKolecka - self.tloustka
                self.wheelChange = True

        #umoznime pohyb ve viewportu pri tahani druheho bodu koty
        if self.currentState != 2:
            if event.type == 'WHEELUPMOUSE' or event.type == 'WHEELDOWNMOUSE' or event.type == 'MIDDLEMOUSE':
                self.snapReset = True
                self.snapFinished = False
                #print('mouse snap reset detection')
                return {'PASS_THROUGH'}
            
        #context.area.tag_redraw()

        #pro cisla na klavesnici
        if self.currentState == 1 or self.currentState == 2:
            #self.wheelChange = True
            if (event.type == 'ZERO' or event.type == 'NUMPAD_0') and event.value == 'RELEASE':
                self.wheelChange = True
                if self.delkaManual == '':
                    self.delkaManual = '0'
                if self.delkaManual.find('.') != -1:
                    self.delkaManual = self.delkaManual + '0'
                if self.delkaManualFloat > 0:
                    self.delkaManual = self.delkaManual + '0'
            
            if (event.type == 'ONE' or event.type == 'NUMPAD_1') and event.value == 'RELEASE':
                self.wheelChange = True
                self.delkaManual = self.delkaManual + '1'
            if (event.type == 'TWO' or event.type == 'NUMPAD_2') and event.value == 'RELEASE':
                self.wheelChange = True
                self.delkaManual = self.delkaManual + '2'
            if (event.type == 'THREE' or event.type == 'NUMPAD_3') and event.value == 'RELEASE':
                self.wheelChange = True
                self.delkaManual = self.delkaManual + '3'
            if (event.type == 'FOUR' or event.type == 'NUMPAD_4') and event.value == 'RELEASE':
                self.wheelChange = True
                self.delkaManual = self.delkaManual + '4'
            if (event.type == 'FIVE' or event.type == 'NUMPAD_5') and event.value == 'RELEASE':
                self.wheelChange = True
                self.delkaManual = self.delkaManual + '5'
            if (event.type == 'SIX' or event.type == 'NUMPAD_6') and event.value == 'RELEASE':
                self.wheelChange = True
                self.delkaManual = self.delkaManual + '6'
            if (event.type == 'SEVEN' or event.type == 'NUMPAD_7') and event.value == 'RELEASE':
                self.wheelChange = True
                self.delkaManual = self.delkaManual + '7'
            if (event.type == 'EIGHT' or event.type == 'NUMPAD_8') and event.value == 'RELEASE':
                self.wheelChange = True
                self.delkaManual = self.delkaManual + '8'
            if (event.type == 'NINE' or event.type == 'NUMPAD_9') and event.value == 'RELEASE':
                self.wheelChange = True
                self.delkaManual = self.delkaManual + '9'

            if (event.type == 'PERIOD' or event.type == 'COMMA' or event.type == 'NUMPAD_PERIOD') and event.value == 'RELEASE':
                self.wheelChange = True
                if self.delkaManual == '':
                    self.delkaManual = '0.'
                if self.delkaManual.find('.') == -1:
                    self.delkaManual = self.delkaManual + '.'

            if (event.type == 'BACK_SPACE') and event.value == 'PRESS':
                self.wheelChange = True
                if self.delkaManual != '':
                    self.delkaManual = self.delkaManual[:-1]

        if (event.type == 'C') and event.value == 'RELEASE':
            if self.continueMode == False:
                self.continueMode = True
                self.continueModeText = 'ON'
            else:
                self.continueMode = False
                self.continueModeText = 'OFF'
            self.textToDrawReDraw()

        if (event.type == 'M') and event.value == 'RELEASE':
                self.snapReset = True
                self.snapFinished = False
                self.edgesMiddleText = 'active'
                if context.scene.DIMENSION.ignoreMid == False:
                    context.scene.DIMENSION.ignoreMid = True
                    self.edgesMiddleText = 'turned off'
                else:
                    context.scene.DIMENSION.ignoreMid = False
                    self.edgesMiddleText = 'active'
                self.textToDrawReDraw()

        #nastavime manual length
        if(self.delkaManual != ''): #nastavime manual length
            if context.scene.DIMENSION.jednotky == 'm' or context.scene.DIMENSION.jednotky == 'None':
                self.delkaManualFloat = float(self.delkaManual)
            if context.scene.DIMENSION.jednotky == 'mm':
                self.delkaManualFloat = float(self.delkaManual) / 1000
            if context.scene.DIMENSION.jednotky == 'cm':
                self.delkaManualFloat = float(self.delkaManual) / 100
            if context.scene.DIMENSION.jednotky == 'dm':
                self.delkaManualFloat = float(self.delkaManual) / 10
            if context.scene.DIMENSION.jednotky == 'km':
                self.delkaManualFloat = float(self.delkaManual) * 1000
            if context.scene.DIMENSION.jednotky == 'ft in':
                self.delkaManualFloat = float(self.delkaManual) * 0.0254
            if context.scene.DIMENSION.jednotky == 'inches':
                self.delkaManualFloat = float(self.delkaManual) * 0.0254
        else: 
            self.delkaManualFloat = 0.0

        #nacitani snap bodu
        if self.snapFinished == False: 
            #print('snap loop')
            self.timeStart = timer()
            if self.snapReset == True:#resets objects iterator, binTree, vertices iterator, objects state, vertices state
                self.binTreeInstance = binTree(0, 0, 1, 'prvni') #tohle snad rovnou zahazuje stary binTree
                self.snapObjectsState = False
                self.snapVerticesState = False
                self.snapMiddlesState = False
                self.snapObjectsIterator = 0
                self.snapVerticeIterator = 0
                self.snapMiddlesIterator = 0
                self.snapReset = False
                self.velikostStromu = 0
                self.counterStredy = -1
                self.listStredu.clear()
                #print('snap reset DONE')

            boolSkipStredy = False #tohle mozna osetrime jako volbu v UI
            if context.scene.DIMENSION.ignoreMid == True:
                boolSkipStredy = True

            regionSizeX = context.area.width
            regionSizeY = context.area.height

            #for object in context.scene.objects: #loop pro jednotlive objekty
            pocetObjektu = len(context.scene.objects)

            counterObjektLoop = 0

            while self.snapObjectsIterator < pocetObjektu:

                #print(self.snapObjectsIterator)

                #prerusime prochazeni objektu (hodne skrytych a non Mesh type)
                counterObjektLoop += 1
                if counterObjektLoop > 10:
                    self.timeStop = timer()
                    if self.timeStop - self.timeStart > 0.01:
                        #continue
                        break


                object = context.scene.objects[self.snapObjectsIterator]
                    
                maticeGlobal = object.matrix_world

                #skip aktualne tvorene koty
                if self.ObjektKoty != None:
                    if self.ObjektKoty.name == object.name:
                        self.snapObjectsIterator += 1
                        if self.snapObjectsIterator == len(context.scene.objects):
                            self.snapFinished = True
                        continue

                if "dimension" in object.name and object.visible_get() and object.type == 'MESH': #koty vytvorene addonem resime extra - chytame jenom vert 0 a 1
                    #self.listV.clear()
                    vertCoord1 = maticeGlobal @ object.data.vertices[0].co
                    testik = bpy_extras.view3d_utils.location_3d_to_region_2d(context.region, context.space_data.region_3d, vertCoord1, default=None)

                    if testik != None and testik[0]> 0 and testik[1]>0 and testik[0]< regionSizeX and testik[1]< regionSizeY:
                        self.binTreeInstance.add(testik[0],testik[1],object.data.vertices[0].index, object.name)
                        self.velikostStromu += 1

                    vertCoord2 = maticeGlobal @ object.data.vertices[1].co
                    testik = bpy_extras.view3d_utils.location_3d_to_region_2d(context.region, context.space_data.region_3d, vertCoord2, default=None)

                    if testik != None and testik[0]> 0 and testik[1]>0 and testik[0]< regionSizeX and testik[1]< regionSizeY:
                        self.binTreeInstance.add(testik[0],testik[1],object.data.vertices[1].index, object.name)
                        self.velikostStromu += 1
                    
                    self.snapObjectsIterator += 1
                    if self.snapObjectsIterator == len(context.scene.objects):
                        self.snapFinished = True
                    continue 


                if object.type == 'MESH' and object.visible_get():
                    #BLOK PRO LIMIT VERT - zatim jenom pro budouci pouziti
                    if boolSkipStredy == True:#zde to chce vypreparovat nejak ty blizke....? -test rychlosti cteni vetices z objektu   udelat switch na snap raycast pri prekroceni limitu, skip invisible vertices, test collections visibility/ mozna rozdelit na raycast mode
                        #for vertex in object.data.vertices: #loop pro jednotlive vert objektu final
                        timeCheckCounter = 0
                        helpBoolMainWhileStop = False
                        if self.snapVerticesState == False:
                            pocetVertices = len(object.data.vertices)
                            while self.snapVerticeIterator < pocetVertices:
                                self.snapVerticesState = False
                                vertex = object.data.vertices[self.snapVerticeIterator]
                                self.snapVerticeIterator += 1
                                timeCheckCounter += 1
                                if vertex.hide == True: #skryte nas nezajimaji
                                    continue
                                vertCoord = maticeGlobal @ vertex.co
                                testik = bpy_extras.view3d_utils.location_3d_to_region_2d(context.region, context.space_data.region_3d, vertCoord, default=None)
                                if testik != None and testik[0]> 0 and testik[1]>0 and testik[0]< regionSizeX and testik[1]< regionSizeY:
                                    self.binTreeInstance.add(testik[0],testik[1],vertex.index, object.name)
                                    self.velikostStromu += 1
                                #tady to musime vsechno prerusit pri prekroceni time limitu
                                if timeCheckCounter > 20:
                                    self.timeStop = timer()
                                    if self.timeStop - self.timeStart > 0.01:
                                        helpBoolMainWhileStop = True
                                        break
                            if helpBoolMainWhileStop == True:#tady jsme vyskocili kvuli prekroceni casu - posleze pokracujeme dal
                                break
                            else: #tady jsme vyskocily z objektu a nulujeme snapVerticeIterator a state bool
                                self.snapVerticeIterator = 0
                                self.snapVerticesState = True #loop verticema je dokoncen

                    else:
                        #for vertex in object.data.vertices: #loop pro jednotlive vert objektu final
                        timeCheckCounter = 0
                        helpBoolMainWhileStop = False
                        if self.snapVerticesState == False:
                            pocetVertices = len(object.data.vertices)
                            while self.snapVerticeIterator < pocetVertices:
                                self.snapVerticesState = False
                                vertex = object.data.vertices[self.snapVerticeIterator]
                                self.snapVerticeIterator += 1
                                timeCheckCounter += 1
                                if vertex.hide == True: #skryte nas nezajimaji
                                    continue
                                vertCoord = maticeGlobal @ vertex.co
                                testik = bpy_extras.view3d_utils.location_3d_to_region_2d(context.region, context.space_data.region_3d, vertCoord, default=None)
                                if testik != None and testik[0]> 0 and testik[1]>0 and testik[0]< regionSizeX and testik[1]< regionSizeY:
                                    self.binTreeInstance.add(testik[0],testik[1],vertex.index, object.name)
                                    self.velikostStromu += 1
                                #tady to musime vsechno prerusit pri prekroceni time limitu
                                if timeCheckCounter > 20:
                                    self.timeStop = timer()
                                    if self.timeStop - self.timeStart > 0.01:
                                        helpBoolMainWhileStop = True
                                        break
                            if helpBoolMainWhileStop == True:#tady jsme vyskocili kvuli prekroceni casu - posleze pokracujeme dal
                                break
                            else: #tady jsme vyskocily z objektu a nulujeme snapVerticeIterator a state bool
                                self.snapVerticeIterator = 0
                                self.snapVerticesState = True #loop verticema je dokoncen
                       

                        #BLOK PRO STREDY EDGES
                        #for edge in object.data.edges:
                        timeCheckCounter = 0
                        helpBoolMainWhileStop = False
                        pocetEdges = len(object.data.edges)
                        while self.snapMiddlesIterator < pocetEdges:
                            #print(self.snapMiddlesIterator)
                            #print(pocetEdges)
                            edge = object.data.edges[self.snapMiddlesIterator]
                            self.snapMiddlesIterator += 1
                            timeCheckCounter += 1
                            if object.data.vertices[int(edge.vertices[0].numerator)].hide == True or object.data.vertices[int(edge.vertices[1].numerator)].hide == True:
                                continue
                            vertCoord1 = maticeGlobal @ object.data.vertices[int(edge.vertices[0].numerator)].co 
                            vertCoord2 = maticeGlobal @ object.data.vertices[int(edge.vertices[1].numerator)].co
                            vertCoord = self.vratBodMeziDvemaBody(vertCoord1,vertCoord2)
                            #self.listStredu.append(vertCoord)
                            stred2D = bpy_extras.view3d_utils.location_3d_to_region_2d(context.region, context.space_data.region_3d, vertCoord, default=None)
                            if stred2D != None and stred2D[0]> 0 and stred2D[1]>0 and stred2D[0]< regionSizeX and stred2D[1]< regionSizeY:
                                self.binTreeInstance.add(stred2D[0],stred2D[1],self.counterStredy, object.name)
                                self.velikostStromu += 1
                                self.counterStredy = self.counterStredy - 1
                                self.listStredu.append(vertCoord)
                            if timeCheckCounter > 10:
                                self.timeStop = timer()
                                if self.timeStop - self.timeStart > 0.01:
                                    helpBoolMainWhileStop = True
                                    break
                        if helpBoolMainWhileStop == True:#tady jsme vyskocili kvuli prekroceni casu - posleze pokracujeme dal
                            break
                        else:
                            self.snapMiddlesIterator = 0
                        #KONEC BLOKU PRO STREDY EDGES

                        #state object a middle asi nebude treba...
                self.snapObjectsIterator += 1
                self.snapVerticesState = False
                if self.snapObjectsIterator == len(context.scene.objects):
                    self.snapFinished = True
                #musime iterovat objekt counter zde 

            if self.debug == True:
                self.timeStop = timer()
                print('Time elapsed for snap points creation is ' + str((self.timeStop - self.timeStart)*1000))
            #print('BinTree size is ' + str(self.velikostStromu))
            #self.binTreeInstance.vypis(self.binTreeInstance)

        if event.type == 'MOUSEMOVE' or self.wheelChange == True:
            #print(self.listObjektu)
            #print(self.listVertIndexu)
            #print(self.listIDObjektu)
            
            if self.debug == True:
                self.timeItStart = timer()

            self.wheelChange = False #for dimension redraw when mouse wheel is changing odsazeniFromBase

            self.jmenoObjektuKoty = ''
            self.ObjektKoty = None
            self.ObjektTextu = None
            self.osazeno = False
            zapsat = False
            self.middlePoint = False
            self.mouseLocation = event.mouse_region_x, event.mouse_region_y
            counterOb = 0
            counterVe = 0
            rozdilAbsX = 15
            rozdilAbsY = 15

            mouseX = event.mouse_region_x
            mouseY = event.mouse_region_y

            #projdeme binTree
            indexNameList = self.binTreeInstance.lookUp(self.binTreeInstance, mouseX, mouseY)
            #print('lookup mi nasel index ' + str(indexNameList[0]) + ' a ' + str(indexNameList[1]))

            if self.debug == True:
                self.timeItStop = timer()
                print('Time elapsed for snap iteration is ' + str((self.timeItStop - self.timeItStart)*1000))

            if indexNameList[0] != None:
                if indexNameList[0] >= 0:
                    self.osazeno = True
                    self.middlePointHelp = False
                    self.snap2Dfin = (indexNameList[2], indexNameList[3])
                    souradnice3D = context.scene.objects[indexNameList[1]].data.vertices[indexNameList[0]].co #'dimension not found - nekde neco mazu blbe
                    maticeGlobal = context.scene.objects[indexNameList[1]].matrix_world
                    self.snap3Dfin = maticeGlobal @ souradnice3D##
                else: #stred
                    self.osazeno = True
                    self.middlePointHelp = True
                    self.snap2Dfin = (indexNameList[2], indexNameList[3])
                    self.snap3Dfin = self.listStredu[indexNameList[0] + (-1 * 2 * indexNameList[0]) - 1]
            else:
                self.snap2Dfin = self.mouseLocation
                self.snap3Dfin = bpy_extras.view3d_utils.region_2d_to_location_3d(context.region, context.space_data.region_3d, self.mouseLocation, self.lastLocation) 

            self.lastLocation = self.snap3Dfin

            self.vektorFin = self.snap3Dfin.copy()

            if self.lockAxisX == True:
                self.vektorFin[1] = self.prvniBodKotyCoord[1]
            if self.lockAxisY == True:
                self.vektorFin[0] = self.prvniBodKotyCoord[0]
            if self.lockAxisZ == True:
                self.vektorFin[2] = self.prvniBodKotyCoord[2]


            if self.currentState == 1: #currentState 1 je vytvorena kota a na mysi tahame druhy bod koty
                if self.prvniBodKotyCoord == self.vektorFin:
                    self.vektorFin[0] += 0.00001
                    self.vektorFin[1] += 0.00001
                    self.vektorFin[2] += 0.00001
                #pokud je delkaManualFloat>0, musime pomoci vektoru mezi body odsunout ten prvni od druheho na danou delku - prepsat je - to se jeste bude orientovat podle "otocit"
                if self.delkaManualFloat > 0:
                    vektorKotyT = self.smerovyVektor(self.prvniBodKotyCoord, self.vektorFin)
                    if self.otocit == False:
                        self.vektorFin = self.pripoctiNejOsa(self.prvniBodKotyCoord, vektorKotyT, self.delkaManualFloat)
                    else:
                        self.prvniBodKotyCoord = self.pripoctiNejOsa(self.vektorFin, vektorKotyT, self.delkaManualFloat)

                if self.otocit == False:
                    #self.vytvorKotu1([self.prvniBodKotyCoord, self.vektorFin])
                    if context.scene.DIMENSION.dimType == 'Slope':
                        MESH_OT_dimension_two_vert.osadKotuSlope(self, self.listKotaText, [self.prvniBodKotyCoord, self.vektorFin])
                        #MESH_OT_dimension_two_vert.srovnejRotationEulerObjektum(self, self.listKotaText[0], self.listKotaText[1], [self.prvniBodKotyCoord, self.vektorFin])
                    if context.scene.DIMENSION.dimType == 'Slope no overlap':
                        MESH_OT_dimension_two_vert.osadKotuSlopeNo(self, self.listKotaText, [self.prvniBodKotyCoord, self.vektorFin])
                        #MESH_OT_dimension_two_vert.srovnejRotationEulerObjektum(self, self.listKotaText[0], self.listKotaText[1], [self.prvniBodKotyCoord, self.vektorFin])
                    if context.scene.DIMENSION.dimType == 'Arrow in':
                        MESH_OT_dimension_two_vert.osadKotuArrowIn(self, self.listKotaText, [self.prvniBodKotyCoord, self.vektorFin])
                        #MESH_OT_dimension_two_vert.srovnejRotationEulerObjektum(self, self.listKotaText[0], self.listKotaText[1], [self.prvniBodKotyCoord, self.vektorFin])
                    if context.scene.DIMENSION.dimType == 'Arrow open':
                        MESH_OT_dimension_two_vert.osadKotuArrowOpen(self, self.listKotaText, [self.prvniBodKotyCoord, self.vektorFin])
                        #MESH_OT_dimension_two_vert.srovnejRotationEulerObjektum(self, self.listKotaText[0], self.listKotaText[1], [self.prvniBodKotyCoord, self.vektorFin])
                    if context.scene.DIMENSION.dimType == 'Arrow out':
                        MESH_OT_dimension_two_vert.osadKotuArrowOut(self, self.listKotaText, [self.prvniBodKotyCoord, self.vektorFin])
                        #MESH_OT_dimension_two_vert.srovnejRotationEulerObjektum(self, self.listKotaText[0], self.listKotaText[1], [self.prvniBodKotyCoord, self.vektorFin])
                    
                    if self.debug == True:
                        self.timeItStop = timer()
                        print('Time before srovnejRotationEulerObjektum je ' + str((self.timeItStop - self.timeItStart)*1000))

                    #MESH_OT_dimension_two_vert.srovnejRotationEulerObjektum(self, self.listKotaText[0], self.listKotaText[1], [self.prvniBodKotyCoord, self.vektorFin])
                else:
                    #self.vytvorKotu1([self.vektorFin, self.prvniBodKotyCoord])
                    if context.scene.DIMENSION.dimType == 'Slope':
                        MESH_OT_dimension_two_vert.osadKotuSlope(self, self.listKotaText, [self.vektorFin, self.prvniBodKotyCoord])
                        #MESH_OT_dimension_two_vert.srovnejRotationEulerObjektum(self, self.listKotaText[0], self.listKotaText[1], [self.vektorFin, self.prvniBodKotyCoord])
                    if context.scene.DIMENSION.dimType == 'Slope no overlap':
                        MESH_OT_dimension_two_vert.osadKotuSlopeNo(self, self.listKotaText, [self.vektorFin, self.prvniBodKotyCoord])
                    if context.scene.DIMENSION.dimType == 'Arrow in':
                        MESH_OT_dimension_two_vert.osadKotuArrowIn(self, self.listKotaText, [self.vektorFin, self.prvniBodKotyCoord])
                    if context.scene.DIMENSION.dimType == 'Arrow open':
                        MESH_OT_dimension_two_vert.osadKotuArrowOpen(self, self.listKotaText, [self.vektorFin, self.prvniBodKotyCoord])
                    if context.scene.DIMENSION.dimType == 'Arrow out':
                        MESH_OT_dimension_two_vert.osadKotuArrowOut(self, self.listKotaText, [self.vektorFin, self.prvniBodKotyCoord])

                    if self.debug == True:
                        self.timeItStop = timer()
                        print('Time before srovnejRotationEulerObjektum je ' + str((self.timeItStop - self.timeItStart)*1000))

                    #MESH_OT_dimension_two_vert.srovnejRotationEulerObjektum(self, self.listKotaText[0], self.listKotaText[1], [self.vektorFin, self.prvniBodKotyCoord])

            if self.currentState == 2: #currentState 2 tahame odsazeni vytvorene koty
                if self.prvniBodKotyCoord == self.vektorFin:
                    self.vektorFin[0] += 0.00001
                    self.vektorFin[1] += 0.00001
                    self.vektorFin[2] += 0.00001

                #testujeme otoceni
                if self.otocit == False:
                    bod1 = self.prvniBodKotyCoord.copy()
                    bod2 = self.druhyBodKotyCoord.copy()
                else:
                    bod1 = self.druhyBodKotyCoord.copy()
                    bod2 = self.prvniBodKotyCoord.copy()

                #prostrelujeme plane na stanoveni mysi na rovine koty
                if self.osazeno == True:
                    vectorViewToMouse = mathutils.Vector((0.0, 0.0, 1.0))
                    #toto jest pro pripad kdy je kota svisle
                    if bod1[0] == bod2[0] and bod1[1] == bod2[1]:
                        vectorViewToMouse = mathutils.Vector((0.0, 1.0, 0.0))
                    viewPointInSpaceCoords = self.snap3Dfin
                    #print(self.ObjektFaceRayCast.bound_box)
                    success, location, normal, face_index = self.ObjektFaceRayCast.ray_cast(viewPointInSpaceCoords, vectorViewToMouse)
                    if success == False:
                        vectorViewToMouse = mathutils.Vector((0.0, 0.0, -1.0))
                        #toto jest pro pripad kdy je kota svisle
                        if bod1[0] == bod2[0] and bod1[1] == bod2[1]:
                            vectorViewToMouse = mathutils.Vector((0.0, -1.0, 0.0))
                        success, location, normal, face_index = self.ObjektFaceRayCast.ray_cast(viewPointInSpaceCoords, vectorViewToMouse)
                else:
                    vectorViewToMouse = bpy_extras.view3d_utils.region_2d_to_vector_3d(context.region, context.space_data.region_3d, self.mouseLocation)
                    #print(vectorViewToMouse)
                    viewPointInSpaceCoords = bpy_extras.view3d_utils.region_2d_to_origin_3d(context.region, context.space_data.region_3d, self.mouseLocation, clamp=None)
                    #print(viewPointInSpaceCoords)
                    if context.space_data.region_3d.view_perspective == 'CAMERA':
                        viewPointInSpaceCoords[2] = abs(viewPointInSpaceCoords[2])
                    success, location, normal, face_index = self.ObjektFaceRayCast.ray_cast(viewPointInSpaceCoords, vectorViewToMouse)
                    
                #self.objektFirsPoint.location = location
                self.snap3Dfin = location
                
                planeNormal = self.planeNormalZflatLined(bod1, bod2) #pro svislou Z se otoci do X-Y
                self.odsazZakl = mathutils.geometry.distance_point_to_plane(location, bod1, planeNormal)

                if abs(event.mouse_x - event.mouse_prev_x)>3 or abs(event.mouse_y - event.mouse_prev_y)>3:
                    self.mouseMoved = True

                #pri odsaz 0 a minus otocit a znovu volat modal? - slouzi k prehazovani koty ze strany na stranu
                if success == False and self.mouseMoved == True:
                    #print('otacim')
                    if self.otocit == False:
                        self.otocit = True
                    else:
                        self.otocit = False
                    vektorKoty = self.smerovyVektor(bod2, bod1)
                    velikostOdsazeni = self.vzdalenostMeziDvemaBody(bod2, bod1) * 100
                    self.ObjektFaceRayCast.data.vertices[0].co = self.pripoctiNejOsa(bod1, vektorKoty, velikostOdsazeni) 
                    self.ObjektFaceRayCast.data.vertices[1].co = self.pripoctiNejOsa(bod2, vektorKoty, -velikostOdsazeni) 
                    self.ObjektFaceRayCast.data.vertices[3].co = self.odsad(bod1, vektorKoty, 2, velikostOdsazeni)
                    self.ObjektFaceRayCast.data.vertices[2].co = self.odsad(bod2, vektorKoty, 2, velikostOdsazeni)
                    return {'RUNNING_MODAL'}

                if self.delkaManualFloat > 0:
                    self.odsazZakl = self.delkaManualFloat

                if context.scene.DIMENSION.dimType == 'Slope':
                    if self.mouseMoved == True:
                        MESH_OT_dimension_two_vert.osadKotuSlope(self, self.listKotaText, [bod1, bod2, self.odsazZakl, self.posunKolecka])
                        #MESH_OT_dimension_two_vert.srovnejRotationEulerObjektum(self, self.listKotaText[0], self.listKotaText[1], [bod1, bod2])
                    else:
                        MESH_OT_dimension_two_vert.osadKotuSlope(self, self.listKotaText, [bod1, bod2])
                        #MESH_OT_dimension_two_vert.srovnejRotationEulerObjektum(self, self.listKotaText[0], self.listKotaText[1], [bod1, bod2])
                if context.scene.DIMENSION.dimType == 'Slope no overlap':
                    if self.mouseMoved == True:
                        MESH_OT_dimension_two_vert.osadKotuSlopeNo(self, self.listKotaText, [bod1, bod2, self.odsazZakl, self.posunKolecka])
                    else:
                        MESH_OT_dimension_two_vert.osadKotuSlopeNo(self, self.listKotaText, [bod1, bod2])
                if context.scene.DIMENSION.dimType == 'Arrow in':
                    if self.mouseMoved == True:
                        MESH_OT_dimension_two_vert.osadKotuArrowIn(self, self.listKotaText, [bod1, bod2, self.odsazZakl, self.posunKolecka])
                    else:
                        MESH_OT_dimension_two_vert.osadKotuArrowIn(self, self.listKotaText, [bod1, bod2])


                if context.scene.DIMENSION.dimType == 'Arrow open':
                    if self.mouseMoved == True:
                        MESH_OT_dimension_two_vert.osadKotuArrowOpen(self, self.listKotaText, [bod1, bod2, self.odsazZakl, self.posunKolecka])
                    else:
                        MESH_OT_dimension_two_vert.osadKotuArrowOpen(self, self.listKotaText, [bod1, bod2])

                if context.scene.DIMENSION.dimType == 'Arrow out':
                    if self.mouseMoved == True:
                        MESH_OT_dimension_two_vert.osadKotuArrowOut(self, self.listKotaText, [bod1, bod2, self.odsazZakl, self.posunKolecka])
                    else:
                        MESH_OT_dimension_two_vert.osadKotuArrowOut(self, self.listKotaText, [bod1, bod2])

                if self.debug == True:
                    self.timeItStop = timer()
                    print('Time before srovnejRotationEulerObjektum je ' + str((self.timeItStop - self.timeItStart)*1000))

                #MESH_OT_dimension_two_vert.srovnejRotationEulerObjektum(self, self.listKotaText[0], self.listKotaText[1], [bod1, bod2])

            if self.debug == True:
                self.timeItStop = timer()
                print('Time elapsed for mouse move event is ' + str((self.timeItStop - self.timeItStart)*1000))

        if event.type == 'ESC': 

            self.snapReset = True #tohle resetuje nacteni 3D bodu do 2D screen space
            #if self.currentState == 0:
                #pass
                #bpy.ops.object.delete() 

            if self.currentState == 1 or self.currentState == 2:
                self.currentState = 0
                bpy.ops.object.select_all(action='DESELECT')
                self.listKotaText[0].select_set(True)
                #activ je mesh a jeste mazeme mesh z activ, empty a text
                meshTmp = self.listKotaText[0].data
                #self.ObjektKoty.select_set(True) je selected v teto fazi
                bpy.ops.object.delete() 
                bpy.data.meshes.remove(meshTmp)

                #delete TEXT
                bpy.ops.object.select_all(action='DESELECT')
                curveTmp = self.listKotaText[1].data
                self.listKotaText[1].select_set(True)
                bpy.ops.object.delete() 
                bpy.data.curves.remove(curveTmp)
                #delete empty
                #self.objektFirsPoint.select_set(True)
                #bpy.ops.object.delete()

                #delete raycast plane
                if self.ObjektFaceRayCast != None:
                    self.ObjektFaceRayCast.select_set(True)
                    meshTmp = self.ObjektFaceRayCast.data
                    bpy.ops.object.delete() 
                    bpy.data.meshes.remove(meshTmp)
                    ObjektFaceRayCast = None

            #bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')

            bpy.types.SpaceView3D.draw_handler_remove(self.nevimHandle, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self.nevimHandle2, 'WINDOW')

            return {'FINISHED'}
        
        if (event.type == 'LEFTMOUSE' and event.value == 'RELEASE') or (event.type == 'NUMPAD_ENTER' and event.value == 'RELEASE') or (event.type == 'RET' and event.value == 'RELEASE'):

            self.mouseLocation = event.mouse_region_x, event.mouse_region_y

            if self.currentState == 2:

                bpy.ops.object.select_all(action='DESELECT')
                self.listKotaText[0].select_set(True)
                #activ je mesh a jeste mazeme mesh z activ, empty a text
                meshTmp = self.listKotaText[0].data
                #self.ObjektKoty.select_set(True) je selected v teto fazi
                bpy.ops.object.delete() 
                bpy.data.meshes.remove(meshTmp)

                #delete TEXT
                bpy.ops.object.select_all(action='DESELECT')
                curveTmp = self.listKotaText[1].data
                self.listKotaText[1].select_set(True)
                bpy.ops.object.delete() 
                bpy.data.curves.remove(curveTmp)

                #delete raycast plane
                self.ObjektFaceRayCast.select_set(True)
                meshTmp = self.ObjektFaceRayCast.data
                bpy.ops.object.delete() 
                bpy.data.meshes.remove(meshTmp)
                self.ObjektFaceRayCast = None

                if self.mouseMoved == True: #possible jeden call
                    if context.scene.DIMENSION.dimType == 'Slope':
                        bpy.ops.mesh.dimensiontwovert('INVOKE_DEFAULT', True, boolFromModal = True, bod1 = self.prvniBodKotyCoord.copy(), bod2 = self.druhyBodKotyCoord.copy(), mouseMoved = self.mouseMoved, odsazeniHlavni = self.odsazZakl, odsazeniZakladna = self.posunKolecka, realtimeFinalDraw = True, otocit = self.otocit, boolFirstRun = True)
                    if context.scene.DIMENSION.dimType == 'Slope no overlap':
                        bpy.ops.mesh.dimensiontwovert('INVOKE_DEFAULT', True, boolFromModal = True, bod1 = self.prvniBodKotyCoord.copy(), bod2 = self.druhyBodKotyCoord.copy(), mouseMoved = self.mouseMoved, odsazeniHlavni = self.odsazZakl, odsazeniZakladna = self.posunKolecka, realtimeFinalDraw = True, otocit = self.otocit, boolFirstRun = True)
                    if context.scene.DIMENSION.dimType == 'Arrow out':
                        bpy.ops.mesh.dimensiontwovert('INVOKE_DEFAULT', True, boolFromModal = True, bod1 = self.prvniBodKotyCoord.copy(), bod2 = self.druhyBodKotyCoord.copy(), mouseMoved = self.mouseMoved, odsazeniHlavni = self.odsazZakl, odsazeniZakladna = self.posunKolecka, realtimeFinalDraw = True, otocit = self.otocit, boolFirstRun = True)
                    if context.scene.DIMENSION.dimType == 'Arrow in':
                        bpy.ops.mesh.dimensiontwovert('INVOKE_DEFAULT', True, boolFromModal = True, bod1 = self.prvniBodKotyCoord.copy(), bod2 = self.druhyBodKotyCoord.copy(), mouseMoved = self.mouseMoved, odsazeniHlavni = self.odsazZakl, odsazeniZakladna = self.posunKolecka, realtimeFinalDraw = True, otocit = self.otocit, boolFirstRun = True)
                    if context.scene.DIMENSION.dimType == 'Arrow open':
                        bpy.ops.mesh.dimensiontwovert('INVOKE_DEFAULT', True, boolFromModal = True, bod1 = self.prvniBodKotyCoord.copy(), bod2 = self.druhyBodKotyCoord.copy(), mouseMoved = self.mouseMoved, odsazeniHlavni = self.odsazZakl, odsazeniZakladna = self.posunKolecka, realtimeFinalDraw = True, otocit = self.otocit, boolFirstRun = True)
                else:
                    if context.scene.DIMENSION.dimType == 'Slope':
                        bpy.ops.mesh.dimensiontwovert('INVOKE_DEFAULT', True, boolFromModal = True, bod1 = self.prvniBodKotyCoord.copy(), bod2 = self.druhyBodKotyCoord.copy(), mouseMoved = self.mouseMoved, realtimeFinalDraw = True, otocit = self.otocit, boolFirstRun = True, continueMode = self.continueMode)
                    if context.scene.DIMENSION.dimType == 'Slope no overlap':
                        bpy.ops.mesh.dimensiontwovert('INVOKE_DEFAULT', True, boolFromModal = True, bod1 = self.prvniBodKotyCoord.copy(), bod2 = self.druhyBodKotyCoord.copy(), mouseMoved = self.mouseMoved, realtimeFinalDraw = True, otocit = self.otocit, boolFirstRun = True, continueMode = self.continueMode)
                    if context.scene.DIMENSION.dimType == 'Arrow out':
                        bpy.ops.mesh.dimensiontwovert('INVOKE_DEFAULT', True, boolFromModal = True, bod1 = self.prvniBodKotyCoord.copy(), bod2 = self.druhyBodKotyCoord.copy(), mouseMoved = self.mouseMoved, realtimeFinalDraw = True, otocit = self.otocit, boolFirstRun = True, continueMode = self.continueMode)
                    if context.scene.DIMENSION.dimType == 'Arrow in':
                        bpy.ops.mesh.dimensiontwovert('INVOKE_DEFAULT', True, boolFromModal = True, bod1 = self.prvniBodKotyCoord.copy(), bod2 = self.druhyBodKotyCoord.copy(), mouseMoved = self.mouseMoved, realtimeFinalDraw = True, otocit = self.otocit, boolFirstRun = True, continueMode = self.continueMode)
                    if context.scene.DIMENSION.dimType == 'Arrow open':
                        bpy.ops.mesh.dimensiontwovert('INVOKE_DEFAULT', True, boolFromModal = True, bod1 = self.prvniBodKotyCoord.copy(), bod2 = self.druhyBodKotyCoord.copy(), mouseMoved = self.mouseMoved, realtimeFinalDraw = True, otocit = self.otocit, boolFirstRun = True, continueMode = self.continueMode)

                #bpy.types.SpaceView3D.draw_handler_remove(self.nevimHandle, 'WINDOW')
                #bpy.types.SpaceView3D.draw_handler_remove(self.nevimHandle2, 'WINDOW')

                #pokud self.continueMode = True, tak jedeme dal else: finished
                if self.continueMode == True:
                    self.prvniBodKotyCoord = self.druhyBodKotyCoord
                    if context.scene.DIMENSION.dimType == 'Slope':
                        self.listKotaText = MESH_OT_dimension_two_vert.vytvorKotuSlope(self)
                    if context.scene.DIMENSION.dimType == 'Slope no overlap':
                        self.listKotaText = MESH_OT_dimension_two_vert.vytvorKotuSlopeNo(self)
                    if context.scene.DIMENSION.dimType == 'Arrow out':
                        self.listKotaText = MESH_OT_dimension_two_vert.vytvorKotuArrowOut(self)
                    if context.scene.DIMENSION.dimType == 'Arrow in':
                        self.listKotaText = MESH_OT_dimension_two_vert.vytvorKotuArrowIn(self)
                    if context.scene.DIMENSION.dimType == 'Arrow open':
                        self.listKotaText = MESH_OT_dimension_two_vert.vytvorKotuArrowOpen(self)
                    self.currentState = 1
                    self.continueModeHelpBool = True
                    self.textToDraw = 'select second point of dimension | (un)lock world axis with X, Y, Z keys | specify length with number keys directly | snaping to edges middle is ' + self.edgesMiddleText + ' - switch with M | continue mode is ' + self.continueModeText + ' - switch with C'
                    self.snapReset = True
                    self.snapFinished = False
                    self.mouseMoved = False
                else:
                    bpy.types.SpaceView3D.draw_handler_remove(self.nevimHandle, 'WINDOW')
                    bpy.types.SpaceView3D.draw_handler_remove(self.nevimHandle2, 'WINDOW')
                    return {'FINISHED'}
            
            #tady tahame vysku koty a koleckem odsazeni
            if self.currentState == 1 and self.continueModeHelpBool == False:
                if self.continueMode == False:
                    self.lockAxisX = False
                    self.lockAxisY = False
                    self.lockAxisZ = False

                self.delkaManual = ''
                if context.scene.DIMENSION.ignoreUndo == True:
                    self.posunKolecka = 0.002*context.scene.DIMENSION.scale #stejna hodnota jako v dimension from 2 verts
                self.currentState = 2
                self.druhyBodKotyCoord = self.vektorFin.copy()

                #setup raycast plane
                bpy.ops.mesh.primitive_plane_add()
                self.ObjektFaceRayCast = context.active_object
                self.ObjektFaceRayCast.hide_set(True)
                ObjektFaceRayCastMesh = self.ObjektFaceRayCast.data
                if self.otocit == False:
                    vektorKoty = self.smerovyVektor(self.prvniBodKotyCoord, self.druhyBodKotyCoord)
                    velikostOdsazeni = self.vzdalenostMeziDvemaBody(self.prvniBodKotyCoord, self.druhyBodKotyCoord) * 100

                    ObjektFaceRayCastMesh.vertices[0].co = self.pripoctiNejOsa(self.prvniBodKotyCoord, vektorKoty, velikostOdsazeni) 
                    ObjektFaceRayCastMesh.vertices[1].co = self.pripoctiNejOsa(self.druhyBodKotyCoord, vektorKoty, -velikostOdsazeni) 
                    ObjektFaceRayCastMesh.vertices[3].co = self.odsad(self.prvniBodKotyCoord, vektorKoty, 2, velikostOdsazeni)
                    ObjektFaceRayCastMesh.vertices[2].co = self.odsad(self.druhyBodKotyCoord, vektorKoty, 2, velikostOdsazeni)
                else:
                    vektorKoty = self.smerovyVektor(self.druhyBodKotyCoord, self.prvniBodKotyCoord)
                    velikostOdsazeni = self.vzdalenostMeziDvemaBody(self.druhyBodKotyCoord, self.prvniBodKotyCoord) * 100

                    ObjektFaceRayCastMesh.vertices[0].co = self.pripoctiNejOsa(self.prvniBodKotyCoord, vektorKoty, velikostOdsazeni) 
                    ObjektFaceRayCastMesh.vertices[1].co = self.pripoctiNejOsa(self.druhyBodKotyCoord, vektorKoty, -velikostOdsazeni) 
                    ObjektFaceRayCastMesh.vertices[3].co = self.odsad(self.prvniBodKotyCoord, vektorKoty, 2, velikostOdsazeni)
                    ObjektFaceRayCastMesh.vertices[2].co = self.odsad(self.druhyBodKotyCoord, vektorKoty, 2, velikostOdsazeni)
                self.edgesMiddleText = 'active'
                if context.scene.DIMENSION.ignoreMid == True:
                    self.edgesMiddleText = 'turned off'
                self.textToDraw = 'move bottom lines with mouse scroll | specify distance from base with mouse, or directly with number keys | snaping to edges middle is ' + self.edgesMiddleText + ' - switch with M | continue mode is ' + self.continueModeText + ' - switch with C'

            self.continueModeHelpBool = False

            #tady jdeme vytvorit kotu (prvni bod na mysi)
            if self.currentState == 0:
                self.prvniBodKotyCoord = self.snap3Dfin.copy()
                if context.scene.DIMENSION.dimType == 'Slope':
                    self.listKotaText = MESH_OT_dimension_two_vert.vytvorKotuSlope(self)
                if context.scene.DIMENSION.dimType == 'Slope no overlap':
                    self.listKotaText = MESH_OT_dimension_two_vert.vytvorKotuSlopeNo(self)
                if context.scene.DIMENSION.dimType == 'Arrow out':
                    self.listKotaText = MESH_OT_dimension_two_vert.vytvorKotuArrowOut(self)
                if context.scene.DIMENSION.dimType == 'Arrow in':
                    self.listKotaText = MESH_OT_dimension_two_vert.vytvorKotuArrowIn(self)
                if context.scene.DIMENSION.dimType == 'Arrow open':
                    self.listKotaText = MESH_OT_dimension_two_vert.vytvorKotuArrowOpen(self)

                self.globalsLoad()
                #pokud rewrite true, tak prepiseme podle UI
                if context.scene.DIMENSION.ignoreUndo == True:
                    self.setupPropsByUI(context)
                    self.globalsSave()
                else:
                    self.setupUnitsScale(context)
                self.currentState = 1

                self.edgesMiddleText = 'active'
                if context.scene.DIMENSION.ignoreMid == True:
                    self.edgesMiddleText = 'turned off'
                self.textToDraw = 'select second point of dimension | (un)lock world axis with X, Y, Z keys | specify length with number keys directly | snaping to edges middle is ' + self.edgesMiddleText + ' - switch with M | continue mode is ' + self.continueModeText + ' - switch with C'

        if event.type == 'X' and event.value == 'RELEASE':
            if self.currentState == 1:
                if self.lockAxisY == True and self.lockAxisZ == True:
                    self.report({'ERROR'}, "Axis Y and Z already locked, please unlock at least one and then you can lock X axis.")
                else:
                    if self.lockAxisX == False:
                        self.lockAxisX = True
                    else:
                        self.lockAxisX = False
        
        if event.type == 'Y' and event.value == 'RELEASE':
            if self.currentState == 1:
                if self.lockAxisX == True and self.lockAxisZ == True:
                    self.report({'ERROR'}, "Axis X and Z already locked, please unlock at least one and then you can lock Y axis.")
                else:
                    if self.lockAxisY == False:
                        self.lockAxisY = True
                    else:
                        self.lockAxisY = False

        if event.type == 'Z' and event.value == 'RELEASE':
            if self.currentState == 1:
                if self.lockAxisX == True and self.lockAxisY == True:
                    self.report({'ERROR'}, "Axis X and Y already locked, please unlock at least one and then you can lock Z axis.")
                else:
                    if self.lockAxisZ == False:
                        self.lockAxisZ = True
                    else:
                        self.lockAxisZ = False

        return {'RUNNING_MODAL'}
    
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
            self.pocetDesetMist = 0
        if context.scene.DIMENSION.jednotky == 'cm':
            self.distanceScale = 100
            self.pocetDesetMist = 2
        if context.scene.DIMENSION.jednotky == 'dm':
            self.distanceScale = 10
            self.pocetDesetMist = 1
        if context.scene.DIMENSION.jednotky == 'm' or context.scene.DIMENSION.jednotky == 'None':
            self.distanceScale = 1
            self.pocetDesetMist = 3
        if context.scene.DIMENSION.jednotky == 'km':
            self.distanceScale = 0.001
            self.pocetDesetMist = 4
        if context.scene.DIMENSION.jednotky == 'ft in':
            self.distanceScale = 1
            self.pocetDesetMist = 0
        if context.scene.DIMENSION.jednotky == 'inches':
            self.distanceScale = 1
            self.pocetDesetMist = 0
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

    def textToDrawReDraw(self):
        if self.currentState == 0:
            self.textToDraw = 'select first point of dimension | snaping to edges middle is ' + self.edgesMiddleText + ' - switch with M | continue mode is ' + self.continueModeText + ' - switch with C'
        if self.currentState == 1:
            self.textToDraw = 'select second point of dimension | (un)lock world axis with X, Y, Z keys | specify length with number keys directly | snaping to edges middle is ' + self.edgesMiddleText + ' - switch with M | continue mode is ' + self.continueModeText + ' - switch with C'
        if self.currentState == 2:
            self.textToDraw = 'move bottom lines with mouse scroll | specify distance from base with mouse, or directly with number keys | snaping to edges middle is ' + self.edgesMiddleText + ' - switch with M | continue mode is ' + self.continueModeText + ' - switch with C'

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

class MESH_OT_remake_dimension(bpy.types.Operator):
    """Remake dimension."""
    bl_idname = "mesh.remakedimension"
    bl_label = "Remake dimension"
    bl_options = {'REGISTER'}

    otocit: bpy.props.BoolProperty(name="switch sides",description="switch to other side",default = False,) #type: ignore
    odsazeniHlavni: bpy.props.FloatProperty(name="dimension offset",description="distance of mine line",default=1.4,min = 0,step=1, precision= 3) #type: ignore
    odsazeniZakladna: bpy.props.FloatProperty(name="perpendicular lines bottom offset",description="distance from base",default=0.4,min = 0,step=1, precision= 3) #type: ignore
    presahKolmice: bpy.props.FloatProperty(name="perpendicular lines top length",description="distance above main line",default=0.6,min = 0,step=1, precision= 3) #type: ignore
    pocetDesetMist: bpy.props.IntProperty(name="decimal places",description="number of decimal places",default = 3,min = 0, max = 6) #type: ignore
    textOffset: bpy.props.FloatProperty(name="offset from main line",description="text distance from baseline",default = 0,step=1, precision= 3) #type: ignore
    textOffsetHor: bpy.props.FloatProperty(name="side offset from center",description="text offset from baseline center",default = 0,step=1, precision= 3) #type: ignore
    rotace: bpy.props.IntProperty(name="rotation along base",description="rotate dimension",default = 0,min = -180,max = 180,) #type: ignore
    textRotace: bpy.props.IntProperty(name="rotation along center",description="rotate text",default = 0,min = -180,max = 180,) #type: ignore
    tloustka: bpy.props.FloatProperty(name="line width",description="line width",default=0.1,min = 0,step=1, precision= 3) #type: ignore
    delkaSikmeCar: bpy.props.FloatProperty(name="border sign size",description="border sign size",default=1,min=0,step=1, precision= 3) #type: ignore
    textSize: bpy.props.FloatProperty(name="text size",description="text size",default=1,min=0,step=1, precision= 3) #type: ignore
    distanceScale: bpy.props.FloatProperty(name="scale for distance calc",description="scale for distance calculation",default = 1,min = 0,step=1, precision= 3) #type: ignore
    protazeni: bpy.props.FloatProperty(name="overlap length",description="length of overlap",default=1,min = 0,step=1, precision= 3) #type: ignore

    boolFromModal: bpy.props.BoolProperty(default = False, options={'HIDDEN'}) #type: ignore

    boolFirstRun: bpy.props.BoolProperty(default = True, options={'HIDDEN'}) #type: ignore

    bod1: bpy.props.FloatVectorProperty(options={'HIDDEN'}) #type: ignore
    bod2: bpy.props.FloatVectorProperty(options={'HIDDEN'}) #type: ignore

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def execute(self, context):

        countObjektu = 0
        objectKoty = None
        for object in context.selected_objects:
            countObjektu = countObjektu + 1
            objectKoty = object

        if countObjektu == 0:
            self.report({'ERROR'}, "No object selected, select dimension object")
            return {'CANCELLED'}
        
        if bpy.context.active_object.mode == 'EDIT':
            self.report({'ERROR'}, "Use this button from object mode with dimension object selected")
            return {'CANCELLED'}

        if countObjektu == 0:
            self.report({'ERROR'}, "No object selected, select dimension object")
            return {'CANCELLED'}
        
        if countObjektu > 1:
            self.report({'ERROR'}, "Too many objects selected, select only one dimension object")
            return {'CANCELLED'}
        
        if objectKoty.type != 'MESH':
            self.report({'ERROR'}, "Selected object is not valid dimension (object is not type MESH)")
            return {'CANCELLED'}
        
        #kontrola child text
        countChildren = 0
        objectTextu = None
        for child in objectKoty.children:
            countChildren = countChildren + 1
            objectTextu = child

        if countChildren == 0:
            self.report({'ERROR'}, "Selected object is not valid dimension (child object is missing)")
            return {'CANCELLED'}
        
        if countChildren > 1:
            self.report({'ERROR'}, "Selected object is not valid dimension (object have more then one child object)")
            return {'CANCELLED'}
        
        if objectTextu.type != 'FONT':
            self.report({'ERROR'}, "Selected object is not valid dimension (child object is not type FONT/text)")
            return {'CANCELLED'}
        
        countDetiDeti = 0
        for ditedeite in objectTextu.children:
            countDetiDeti = countDetiDeti + 1
        if countDetiDeti > 0:
            self.report({'ERROR'}, "Selected object is not valid dimension (font object have children)")
            return {'CANCELLED'}
        
        #nejdriv kontrola vertice count - do jendoho z typu, pak face sequence, pokud neshoda, tak CANCEL, pokud shoda, tak nacitame vsechny properties - odsazeniHlavni, odsazeniZakladna, delkaSikmeCar, tloustka, presahKolmice, protazeni, rotace
        meshKoty = objectKoty.data
        #verticesCount = 0
        verticesCount = len(meshKoty.vertices)
        #verticesCount = verticesCount - 1
        #for vert in meshKoty.vertices:
            #verticesCount = verticesCount + 1

        helpBoolForVertCount = False
        
        #SLOPE
        if verticesCount == 50:

            helpBoolForVertCount = True

            listFacesSlope = [[0,1,11,6],[1,0,4,9],[0,6,17,16],[0,16,18,7],[0,7,15,2],[0,2,14,5],[0,5,24,22],[0,22,23,4],[1,9,27,25],[1,25,26,8],[1,8,12,3],[1,3,13,10],[1,10,20,19],[1,19,21,11],[5,34,30,28],[5,28,31,35],[6,29,32,37],[6,36,33,29],[9,44,40,38],
                          [9,38,41,45],[10,39,42,47],[10,46,43,39]]

            faceCount = 0
            for face in meshKoty.polygons:
                vertCount = 0
                for vertex in face.vertices:
                    try:
                        if listFacesSlope[faceCount][vertCount] != vertex:
                            self.report({'ERROR'}, "Selected object is not valid dimension (faces do not much originaly created dimension)")
                            return {'CANCELLED'}
                    except:
                        self.report({'ERROR'}, "Selected object is not valid dimension (faces do not much originaly created dimension)")
                        return {'CANCELLED'}
                    vertCount = vertCount + 1
                faceCount = faceCount + 1

            context.scene.DIMENSION.dimType = 'Slope'

            self.bod1 = objectKoty.matrix_world @ meshKoty.vertices[48].co
            self.bod2 = objectKoty.matrix_world @ meshKoty.vertices[49].co

            self.odsazeniHlavni = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[0].co,meshKoty.vertices[48].co)
            self.odsazeniZakladna = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[16].co,meshKoty.vertices[48].co)
            self.delkaSikmeCar = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[29].co,meshKoty.vertices[28].co)
            self.tloustka = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[17].co,meshKoty.vertices[18].co)
            self.presahKolmice = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[0].co,meshKoty.vertices[22].co)
            self.protazeni = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[0].co,meshKoty.vertices[2].co)
            self.rotace = int(math.degrees(objectKoty.rotation_euler[0]))
            typeTmp = 'Slope'
            testKonec = self.indetifyText(context, objectTextu, objectKoty, meshKoty, typeTmp)
            if testKonec == False:
                self.report({'ERROR'}, "Selected object is not valid dimension (unknown text in annotation)")
                return {'CANCELLED'}
        #SLOPENOOVERLAP
        if verticesCount == 44:

            helpBoolForVertCount = True

            listFacesSlopeNoOverlap = [[0,1,9,6],[1,0,4,8],[0,6,13,12],[0,12,14,2],[0,2,20,18],[0,18,19,4],[5,7,26,24],[5,24,27,30],[6,25,28,32],[6,31,29,25],[8,39,35,33],[8,33,36,40],[1,8,23,21],[1,21,22,3],[10,11,38,34],[10,34,37,41],[1,3,16,15],[1,15,17,9]]

            faceCount = 0
            for face in meshKoty.polygons:
                vertCount = 0
                for vertex in face.vertices:
                    try:
                        if listFacesSlopeNoOverlap[faceCount][vertCount] != vertex:
                            self.report({'ERROR'}, "Selected object is not valid dimension (faces do not much originaly created dimension)")
                            return {'CANCELLED'}
                    except:
                        self.report({'ERROR'}, "Selected object is not valid dimension (faces do not much originaly created dimension)")
                        return {'CANCELLED'}
                    vertCount = vertCount + 1
                faceCount = faceCount + 1

            context.scene.DIMENSION.dimType = 'Slope no overlap'

            self.bod1 = objectKoty.matrix_world @ meshKoty.vertices[42].co
            self.bod2 = objectKoty.matrix_world @ meshKoty.vertices[43].co

            self.odsazeniHlavni = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[0].co,meshKoty.vertices[42].co)
            self.odsazeniZakladna = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[12].co,meshKoty.vertices[42].co)
            self.delkaSikmeCar = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[25].co,meshKoty.vertices[24].co)
            self.tloustka = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[13].co,meshKoty.vertices[14].co)
            self.presahKolmice = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[0].co,meshKoty.vertices[18].co)
            self.protazeni = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[0].co,meshKoty.vertices[18].co)
            self.rotace = int(math.degrees(objectKoty.rotation_euler[0]))
            typeTmp = 'Slope no overlap'
            testKonec = self.indetifyText(context, objectTextu, objectKoty, meshKoty, typeTmp)
            if testKonec == False:
                self.report({'ERROR'}, "Selected object is not valid dimension (unknown text in annotation)")
                return {'CANCELLED'}

        #ARROWIN and ARROWOUT
        if verticesCount == 30:

            helpBoolForVertCount = True

            listFacesArrowIn = [[0,1,7,5],[0,4,6,1],[0,5,9,8],[0,8,10,2],[0,2,16,14],[0,14,15,4],[4,20,22],[5,23,21],[1,3,12,11],[1,11,13,7],[7,25,27],[6,26,24],[1,6,19,17],[1,17,18,3]]
            listFacesArrowOut = [[0,1,6,5],[0,4,7,1],[0,5,11,10],[0,10,12,2],[0,2,23,24],[0,24,22,3],[0,3,18,16],[0,16,17,4],[1,9,14,13],[1,13,15,6],[1,7,21,19],[1,19,20,8],[1,8,25,27],[1,27,26,9]]

            intType = 0 #0 zadny, 1 arrowIn, 2 arrowOut

            faceCount = 0
            intType = 1
            for face in meshKoty.polygons:
                vertCount = 0
                for vertex in face.vertices:
                    try:
                        if listFacesArrowIn[faceCount][vertCount] != vertex:
                            intType = 0
                    except:
                        intType = 0
                    vertCount = vertCount + 1
                faceCount = faceCount + 1
            if intType == 0:
                faceCount = 0
                intType = 2
                for face in meshKoty.polygons:
                    vertCount = 0
                    for vertex in face.vertices:
                        try:
                            if listFacesArrowOut[faceCount][vertCount] != vertex:
                                intType = 0
                        except:
                            intType = 0
                        vertCount = vertCount + 1
                    faceCount = faceCount + 1

            if intType == 1:#delame arrowin complet

                context.scene.DIMENSION.dimType = 'Arrow in'

                self.bod1 = objectKoty.matrix_world @ meshKoty.vertices[28].co
                self.bod2 = objectKoty.matrix_world @ meshKoty.vertices[29].co

                self.odsazeniHlavni = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[0].co,meshKoty.vertices[28].co)
                self.odsazeniZakladna = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[8].co,meshKoty.vertices[28].co)
                self.delkaSikmeCar = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[4].co,meshKoty.vertices[20].co)
                self.delkaSikmeCar = self.delkaSikmeCar/0.7
                self.tloustka = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[9].co,meshKoty.vertices[10].co)
                self.presahKolmice = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[0].co,meshKoty.vertices[14].co)
                self.protazeni = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[0].co,meshKoty.vertices[14].co)
                self.rotace = int(math.degrees(objectKoty.rotation_euler[0]))
                typeTmp = 'Arrow in out'
                testKonec = self.indetifyText(context, objectTextu, objectKoty, meshKoty, typeTmp)
                if testKonec == False:
                    self.report({'ERROR'}, "Selected object is not valid dimension (unknown text in annotation)")
                    return {'CANCELLED'}

            elif intType == 2: #delame arrowout complet

                context.scene.DIMENSION.dimType = 'Arrow out'

                self.bod1 = objectKoty.matrix_world @ meshKoty.vertices[28].co
                self.bod2 = objectKoty.matrix_world @ meshKoty.vertices[29].co

                self.odsazeniHlavni = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[0].co,meshKoty.vertices[28].co)
                self.odsazeniZakladna = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[10].co,meshKoty.vertices[28].co)
                self.delkaSikmeCar = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[3].co,meshKoty.vertices[22].co)
                self.delkaSikmeCar = self.delkaSikmeCar/0.7
                self.tloustka = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[11].co,meshKoty.vertices[12].co)
                self.presahKolmice = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[0].co,meshKoty.vertices[16].co)
                self.protazeni = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[0].co,meshKoty.vertices[16].co)
                self.rotace = int(math.degrees(objectKoty.rotation_euler[0]))
                typeTmp = 'Arrow in out'
                testKonec = self.indetifyText(context, objectTextu, objectKoty, meshKoty, typeTmp)
                if testKonec == False:
                    self.report({'ERROR'}, "Selected object is not valid dimension (unknown text in annotation)")
                    return {'CANCELLED'}
            
            elif intType == 0: #cancel
                self.report({'ERROR'}, "Selected object is not valid dimension (faces do not much originaly created dimension)")
                return {'CANCELLED'}

        #ARROWOPEN
        if verticesCount == 34:

            helpBoolForVertCount = True

            listFacesArrowOpen = [[0,1,7,5],[0,4,6,1],[0,5,9,8],[0,8,10,2],[0,2,16,14],[0,14,15,4],[4,20,22,24],[5,25,23,21],[1,3,12,11],[1,11,13,7],[7,27,29,31],[6,30,28,26],[1,6,19,17],[1,17,18,3]]

            faceCount = 0
            for face in meshKoty.polygons:
                vertCount = 0
                for vertex in face.vertices:
                    try:
                        if listFacesArrowOpen[faceCount][vertCount] != vertex:
                            self.report({'ERROR'}, "Selected object is not valid dimension (faces do not much originaly created dimension)")
                            print(faceCount)
                            print(vertCount)
                            return {'CANCELLED'}
                    except:
                        self.report({'ERROR'}, "Selected object is not valid dimension (faces do not much originaly created dimension)")
                        return {'CANCELLED'}
                    vertCount = vertCount + 1
                faceCount = faceCount + 1

            context.scene.DIMENSION.dimType = 'Arrow open'

            self.bod1 = objectKoty.matrix_world @ meshKoty.vertices[32].co
            self.bod2 = objectKoty.matrix_world @ meshKoty.vertices[33].co

            self.odsazeniHlavni = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[0].co,meshKoty.vertices[32].co)
            self.odsazeniZakladna = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[8].co,meshKoty.vertices[32].co)
            self.delkaSikmeCar = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[4].co,meshKoty.vertices[20].co)
            self.delkaSikmeCar =  self.delkaSikmeCar * 2
            self.tloustka = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[9].co,meshKoty.vertices[10].co)
            self.presahKolmice = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[0].co,meshKoty.vertices[14].co)
            self.protazeni = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[0].co,meshKoty.vertices[14].co)
            self.rotace = int(math.degrees(objectKoty.rotation_euler[0]))
            typeTmp = 'Arrow open'
            testKonec = self.indetifyText(context, objectTextu, objectKoty, meshKoty, typeTmp)
            if testKonec == False:
                self.report({'ERROR'}, "Selected object is not valid dimension (unknown text in annotation)")
                return {'CANCELLED'}

        if helpBoolForVertCount == False:
            self.report({'ERROR'}, "Selected object is not valid dimension (unknown number of vertices)")
            return {'CANCELLED'}

        bpy.ops.object.select_all(action='DESELECT')
        meshTmp = objectKoty.data
        objectKoty.select_set(True)
        bpy.ops.object.delete() 
        bpy.data.meshes.remove(meshTmp)

        bpy.ops.object.select_all(action='DESELECT')
        curveTmp = objectTextu.data
        objectTextu.select_set(True)
        bpy.ops.object.delete() 
        bpy.data.curves.remove(curveTmp)

        #call na tvorbu pro vsechny spolecnej... setup UI
        #bpy.ops.mesh.dimensiontwovert('INVOKE_DEFAULT', True, boolFromModal = True, bod1 = self.bod1, bod2 = self.bod2, boolFirstRun = True)

        #context.scene.DIMENSION.ignoreUndo = False

        bpy.ops.mesh.dimensiontwovert(True, boolFromModal = True, boolRemakeOP = True, bod1 = self.bod1, bod2 = self.bod2, boolFirstRun = True, odsazeniHlavni = self.odsazeniHlavni, odsazeniZakladna = self.odsazeniZakladna, delkaSikmeCar = self.delkaSikmeCar,
                                   tloustka = self.tloustka, presahKolmice = self.presahKolmice, protazeni = self.protazeni, rotace = self.rotace, textSize = self.textSize, pocetDesetMist = self.pocetDesetMist, textOffset = self.textOffset,
                                   textOffsetHor = self.textOffsetHor, textRotace = self.textRotace, distanceScale = self.distanceScale, otocit = False)

        return {'FINISHED'}

    def indetifyText(self, context, objectTextu, objectKoty, meshKoty, typeTmp) -> bool:

        self.textSize = objectTextu.data.size
        textKoty = MESH_OT_dimension_two_vert.vymenCarkuZaTecku(self,objectTextu.data.body)
        jednotky = self.vratJednotkyZCisla(textKoty)
        #print(jednotky)
        if jednotky == "":
            jednotky = "None"
        if jednotky == "ftin":
            jednotky = 'ft in'
            context.scene.DIMENSION.showUnits = True
        if jednotky == "in":
            jednotky = 'inches'
            context.scene.DIMENSION.showUnits = True
        if jednotky == "\'\"":
            jednotky = 'ft in'
        if jednotky == "\"":
            jednotky = 'inches'
            context.scene.DIMENSION.showUnits = False
        if jednotky != 'None' and jednotky != 'ft in' and jednotky != 'inches' and jednotky != 'km' and jednotky != 'm' and jednotky != 'dm' and jednotky != 'cm' and jednotky != 'mm':
            #print(jednotky + 'D')
            return False
        else:
            context.scene.DIMENSION.jednotky = jednotky
        if jednotky == 'ft in':
            textKoty = self.vratCisloJakoTextZeStringuImp(textKoty) #mezi foot a inch mezera
        else:
            textKoty = self.vratCisloJakoTextZeStringu(textKoty)
        self.pocetDesetMist = self.vratPocetDesetinychMist(textKoty)
        self.textOffset = objectTextu.data.offset_y
        self.textOffsetHor = objectTextu.data.offset_x
        #budeme otacet po jednom stupni dokud nenajdeme shodu?
        uhel = -180
        rotaceZaloha = objectTextu.rotation_euler.copy()
        shodaRotace = False
        self.textRotace = 0
        for i in range(361):
            shodaRotace = True
            objectTextu.rotation_euler.rotate_axis("Z", math.radians(uhel + i))
            for ind in range(3):
                if math.isclose(objectTextu.rotation_euler[ind], objectKoty.rotation_euler[ind], abs_tol=0.00001) == False:
                    shodaRotace = False
                    objectTextu.rotation_euler = rotaceZaloha
                    break
            if shodaRotace == True:
                self.textRotace = -(uhel + i)
                objectTextu.rotation_euler = rotaceZaloha
                break
            objectTextu.rotation_euler = rotaceZaloha
        if jednotky == 'ft in':
            cisloKoty = self.stringFtInToInches(textKoty) #cislo koty je v inches
        else:
            cisloKoty = float(textKoty)
        tmpBod1 = 0
        tmpBod2 = 0
        if typeTmp == 'Slope':
            tmpBod1 = 49
            tmpBod2 = 48
        if typeTmp == 'Slope no overlap':
            tmpBod1 = 43
            tmpBod2 = 42
        if typeTmp == 'Arrow in out':
            tmpBod1 = 29
            tmpBod2 = 28
        if typeTmp == 'Arrow open':
            tmpBod1 = 33
            tmpBod2 = 32
        vzalenostBaseBodu = MESH_OT_dimension_two_vert.vzdalenostMeziDvemaBody(self,meshKoty.vertices[tmpBod1].co,meshKoty.vertices[tmpBod2].co)
        context.scene.DIMENSION.fontsArray = objectTextu.data.font.name
        pomerCisel = round(cisloKoty/vzalenostBaseBodu,6)
        helpBoolFit = False
        if math.isclose(pomerCisel, 1, abs_tol=0.01) == True:
            self.distanceScale = 1
            context.scene.DIMENSION.jednotky = 'm'
            context.scene.DIMENSION.showUnits = True
            helpBoolFit = True
            if jednotky == 'None':
                context.scene.DIMENSION.showUnits = False
        if math.isclose(pomerCisel, 0.001, abs_tol=0.0005) == True:
            self.distanceScale = 0.001
            context.scene.DIMENSION.jednotky = 'km'
            context.scene.DIMENSION.showUnits = True
            helpBoolFit = True
            if jednotky == 'None':
                context.scene.DIMENSION.showUnits = False
        if math.isclose(pomerCisel, 10, abs_tol=2) == True:
            self.distanceScale = 10
            context.scene.DIMENSION.jednotky = 'dm'
            context.scene.DIMENSION.showUnits = True
            helpBoolFit = True
            if jednotky == 'None':
                context.scene.DIMENSION.showUnits = False
        if math.isclose(pomerCisel, 100, abs_tol=6) == True:
            self.distanceScale = 100
            context.scene.DIMENSION.jednotky = 'cm'
            context.scene.DIMENSION.showUnits = True
            helpBoolFit = True
            if jednotky == 'None':
                context.scene.DIMENSION.showUnits = False
        if math.isclose(pomerCisel, 39.370078, abs_tol=6) == True:
            self.distanceScale = 1
            helpBoolFit = True
        if math.isclose(pomerCisel, 1000, abs_tol=50) == True:
            self.distanceScale = 1000
            context.scene.DIMENSION.jednotky = 'mm'
            context.scene.DIMENSION.showUnits = True
            helpBoolFit = True
            if jednotky == 'None':
                context.scene.DIMENSION.showUnits = False
        if helpBoolFit == False:
            self.distanceScale = pomerCisel
        return True

    def stringFtInToInches(self, text: str) -> float:
        cisloFoot = ''
        cisloInch = ''
        afterSwitch = False
        for character in text:
            if character == ' ':
                afterSwitch = True
                continue
            if afterSwitch == True:
                cisloInch = cisloInch + character
            if afterSwitch == False:
                cisloFoot = cisloFoot + character
        vysledek = 0.0
        vysledek = (float(cisloFoot)*12) + float(cisloInch)
        return vysledek

    def vratPocetDesetinychMist(self, text: str) -> int:
        pocetDesetMist = 0
        afterSwitch = False
        for character in text:
            if afterSwitch == True:
                pocetDesetMist = pocetDesetMist + 1
            if character == ',' or character == '.':
                afterSwitch = True
        return pocetDesetMist
    
    def vratCisloJakoTextZeStringu(self, text: str) -> str:
        vysledek = ""
        for character in text:
            if character.isnumeric() or character == ',' or character == '.':
                vysledek = vysledek + character
        return vysledek    

    def vratCisloJakoTextZeStringuImp(self, text: str) -> str:
        vysledek = ""
        for character in text:
            if character.isnumeric() or character == ',' or character == '.':
                vysledek = vysledek + character
            elif character == "\'" or character == "t":
                vysledek = vysledek + ' '
        return vysledek    
    
    def vratJednotkyZCisla(self, text: str) -> str:
        vysledek = ""
        for character in text:
            if character.isalpha():
                vysledek = vysledek + character
            if character == '\'' or character == '\"':
                vysledek = vysledek + character
        return vysledek   

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

class binTree(): #prvni prvek | eventuelne dopsat delete | stredy maji zaporne integery - prvni je -1 (nulty v listu 3D souradnic)
    x = 0.0
    y = 0.0
    vertIndex = 0
    objectName = ''
    leftChild = None
    rightChild = None

    def __init__(self, x: float, y: float, vertIndex: int, objectName: str):
        self.x = x
        self.y = y
        self.vertIndex = vertIndex
        self.objectName = objectName
        leftChild = None
        rightChild = None
    
    def add(self, x: float, y: float, vertIndex: int, objectName: str):
        #osetrime prazdny strom
        if self.x == 0.0:
            #print('pridan nulty x: ' + str(x))
            self.x = x
            self.y = y
            self.vertIndex = vertIndex
            self.objectName = objectName
            return

        novyPrvek = binTree(x, y, vertIndex, objectName)
        boolRun = True
        safeCounter = 0
        actualList = self
        #prvniStejny = None

        while boolRun == True:
            safeCounter = safeCounter + 1
            if safeCounter > 10000000:
                boolRun = False

            if x > actualList.x:
                if actualList.rightChild==None:
                    actualList.rightChild = novyPrvek
                    #print('za index: ' + str(actualList.vertIndex) + ' x: ' + str(actualList.x) + ' pridan rightChild x: ' + str(x) + ' index ' + str(vertIndex))
                    boolRun = False
                    return
                else:
                    actualList = actualList.rightChild
                    continue

            if x < actualList.x: 
                if actualList.rightChild != None:#zmena...
                    if actualList.x == actualList.rightChild.x:
                        actualList = actualList.rightChild
                        continue

                if actualList.leftChild==None:
                    actualList.leftChild = novyPrvek
                    #print('za index: ' + str(actualList.vertIndex) + ' x: ' + str(actualList.x) + ' pridan leftChild x: ' + str(x) + ' index ' + str(vertIndex))
                    boolRun = False
                    return   
                else:
                    actualList = actualList.leftChild
                    continue
            
            if x == actualList.x:
                #pokud je vpravo empty, tak pridame novy prvek vpravo a presuneme tam leftChild

                if actualList.rightChild == None:
                    actualList.rightChild = novyPrvek
                    actualList.rightChild.leftChild = actualList.leftChild
                    actualList.leftChild = None
                    boolRun = False
                    return   
                #dokud vpravo neni empty, tak testujeme : A) jestli je stejny, tak se posuneme na nej a continue (tzn. ze musime bud pokazde prehazovat left, nebo si pamatovat pred while prvni leftChild a na konci ten puvodni leftChild dat None)
                if actualList.rightChild.x == actualList.x:
                    actualList = actualList.rightChild
                    continue
                else:# B) jeslti neni stejny, tak vlozime mezi a opet musime presunout leftChild 
                    zalohaRightChild = actualList.rightChild
                    actualList.rightChild = novyPrvek
                    actualList.rightChild.rightChild = zalohaRightChild
                    actualList.rightChild.leftChild = actualList.leftChild
                    actualList.leftChild = None
                    boolRun = False
                    return   
    
    def lookUp(self, aktInstance, x: float, y: float) -> list: #budeme ukladat x +-15, ale s nejakym limitem... treba 100 zatim.... odzkouset na velke scene.... a z tech ulozenych iterujeme closest y? testovat 
        searchActive = True
        listCloseX = []
        limit = 100
        listCloseXCounter = 0
        counter = 0

        while searchActive == True:

            counter = counter + 1
            if x > (aktInstance.x - 15) and x < (aktInstance.x + 15):
                if y > (aktInstance.y - 15) and y < (aktInstance.y + 15):
                    listCloseX.append(aktInstance)
                    listCloseXCounter = listCloseXCounter + 1
                    if listCloseXCounter > limit:#vyskocime z prohledavani stromu pokud ma 100 snapu a vic (asi pak snizime)
                        searchActive = False

            if aktInstance.leftChild != None and x < aktInstance.x:
                aktInstance = aktInstance.leftChild
                continue

            if aktInstance.leftChild == None and x < aktInstance.x:#zmena?
                if aktInstance.rightChild != None:
                    aktInstance = aktInstance.rightChild
                    continue

            if aktInstance.rightChild != None and x >= aktInstance.x:
                aktInstance = aktInstance.rightChild
                continue

            if aktInstance.rightChild == None and x >= aktInstance.x:#zmena?
                if aktInstance.leftChild != None:
                    aktInstance = aktInstance.leftChild
                    continue

            if aktInstance.rightChild == None and aktInstance.leftChild == None:
                searchActive = False
                continue
        
        #print('close points are: ' + str(listCloseXCounter))
        #print('prosli jsme v bintree listu: ' + str(counter))

        #projdeme list snapu a hledame nejblizsi....
        vzdalenostTmp = 30
        if listCloseXCounter > 0:
            nejblizsiAktual = listCloseX[0]
        for listMember in listCloseX:
            vzdalenostTmpOld = vzdalenostTmp
            vzdalenostTmp = self.vzdalenostMeziDvema2DBody([x,y],[listMember.x,listMember.y])
            if vzdalenostTmp < vzdalenostTmpOld:
                nejblizsiAktual = listMember

        if listCloseXCounter > 0:
            return [nejblizsiAktual.vertIndex, nejblizsiAktual.objectName, nejblizsiAktual.x, nejblizsiAktual.y]
        else:
            return [None, None]

    def vypis(self, aktInstance):
        print('')
        print(aktInstance.objectName)
        print(aktInstance.vertIndex)
        print(aktInstance.x)
        print(aktInstance.y)
        if aktInstance.leftChild != None:
            print('leftChild ' + str(aktInstance.leftChild.vertIndex))
        if aktInstance.rightChild != None:
            print('rightChild ' + str(aktInstance.rightChild.vertIndex))

        if aktInstance.leftChild != None:
            self.vypis(aktInstance.leftChild)
        if aktInstance.rightChild != None:
            self.vypis(aktInstance.rightChild)
        return
    
    def vzdalenostMeziDvema2DBody(self, bod1: list[float], bod2: list[float]) -> float:
        del1 = bod1[0] - bod2[0]
        del2 = bod1[1] - bod2[1]
        vysledekSq = (del1*del1) + (del2*del2)
        vysledek = math.sqrt(vysledekSq)

        return vysledek

blender_classes = [VIEW3D_PT_dimensions,
                lines_operators.MESH_OT_lines,
                lines_operators.MESH_OT_lines_clear,
                MESH_OT_dimension_two_vert,
                SFA_OT_realtime_dimension,
                DIMENSION_GLOBALS,
                cameras_setup.CAMERA_DIMSELECT,
                cameras_setup.CAMERA_DimSetupCam,
                hatches_operator.MESH_OT_hatches,
                MESH_OT_remake_dimension]

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
    
    