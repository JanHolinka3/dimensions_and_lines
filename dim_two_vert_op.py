import bpy #type:ignore
import bmesh #type:ignore
import mathutils #type:ignore
import math
from . import functions
from . import dimSlope
from timeit import default_timer as timer

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
            listKotaText = dimSlope.vytvorKotuSlope()
            self.ObjektKoty = listKotaText[0]
            self.ObjektTextu = listKotaText[1]
            dimSlope.osadKotuSlope(self, listKotaText, listveci)
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