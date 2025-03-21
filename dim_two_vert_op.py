import bpy #type:ignore
from . import dimSlope
from . import dimSlopeNo
from . import dimArrowOut
from . import dimArrowIn
from . import dimArrowOpen
from timeit import default_timer as timer

class MESH_OT_dimension_two_vert(bpy.types.Operator):
    """Add dimensions from two selected vertices."""
    bl_idname = "mesh.dimension_two_vert"
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
                if counter > 1: 
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
            listKotaText = dimSlope.vytvorKotuSlope(self)
            dimSlope.osadKotuSlope(self, listKotaText, listveci)
            #self.srovnejRotationEulerObjektum(listKotaText[0], listKotaText[1], listveci)
        if context.scene.DIMENSION.dimType == 'Slope no overlap':
            listKotaText = dimSlopeNo.vytvorKotuSlopeNo(self)  
            dimSlopeNo.osadKotuSlopeNo(self, listKotaText, listveci)
            #self.srovnejRotationEulerObjektum(listKotaText[0], listKotaText[1], listveci)
        if context.scene.DIMENSION.dimType == 'Arrow open':
            listKotaText = dimArrowOpen.vytvorKotuArrowOpen(self)
            dimArrowOpen.osadKotuArrowOpen(self, listKotaText, listveci)
            #self.srovnejRotationEulerObjektum(listKotaText[0], listKotaText[1], listveci)
        if context.scene.DIMENSION.dimType == 'Arrow in':  
            listKotaText = dimArrowIn.vytvorKotuArrowIn(self)
            dimArrowIn.osadKotuArrowIn(self, listKotaText, listveci)
            #self.srovnejRotationEulerObjektum(listKotaText[0], listKotaText[1], listveci)
        if context.scene.DIMENSION.dimType == 'Arrow out':
            listKotaText = dimArrowOut.vytvorKotuArrowOut(self)
            dimArrowOut.osadKotuArrowOut(self, listKotaText, listveci)
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
    