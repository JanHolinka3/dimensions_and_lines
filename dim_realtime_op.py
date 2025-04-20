import bpy #type:ignore
import mathutils #type:ignore
import math
import bmesh #type:ignore
from . import dimSlope
from . import dimSlopeNo
from . import dimArrowOut
from . import dimArrowIn
from . import dimArrowOpen
from . import functions
from . import binTree
from timeit import default_timer as timer
import bpy_extras.view3d_utils # type: ignore
from gpu_extras.batch import batch_for_shader # type: ignore
import gpu # type: ignore
import blf # type: ignore

class MESH_OT_realtime_dimension(bpy.types.Operator): #opravit cursor movement
    """Realtime dimensions."""
    bl_idname='mesh.realtime_dimension'
    bl_label='Create dimensions'

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
                elif self.delkaManualFloat > 0:
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

        #continuus mode
        if (event.type == 'C') and event.value == 'RELEASE':
            if self.continueMode == False:
                self.continueMode = True
                self.continueModeText = 'ON'
            else:
                self.continueMode = False
                self.continueModeText = 'OFF'
            functions.textToDrawReDraw(self)

        #middle point snap on and off
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
                functions.textToDrawReDraw(self)

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
            if self.currentState == 2:
                self.delkaManualFloat = float(self.delkaManual)
        else: 
            self.delkaManualFloat = 0.0

        #nacitani snap bodu
        if self.snapFinished == False: 
            #print('snap loop')
            self.timeStart = timer()
            if self.snapReset == True:#resets objects iterator, binTree, vertices iterator, objects state, vertices state
                self.binTreeInstance = binTree.binTree(0, 0, 1, 'prvni') #tohle snad rovnou zahazuje stary binTree
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
                            vertCoord = functions.vratBodMeziDvemaBody(vertCoord1,vertCoord2)
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
                #pokud je delkaManualFloat>0, musime pomoci vektoru mezi body odsunout ten prvni od druheho na danou delku - prepsat je
                if self.delkaManualFloat > 0:
                    vektorKotyT = functions.smerovyVektor(self.prvniBodKotyCoord, self.vektorFin)
                    #if self.otocit == False:
                        #self.vektorFin = functions.pripoctiNejOsa(self.prvniBodKotyCoord, vektorKotyT, self.delkaManualFloat)
                    #else:
                        #self.prvniBodKotyCoord = functions.pripoctiNejOsa(self.vektorFin, vektorKotyT, self.delkaManualFloat)
                    self.vektorFin = functions.pripoctiNejOsa(self.prvniBodKotyCoord, vektorKotyT, self.delkaManualFloat)

                if self.otocit == False:
                    #self.vytvorKotu1([self.prvniBodKotyCoord, self.vektorFin])
                    if context.scene.DIMENSION.dimType == 'Slope':
                        dimSlope.osadKotuSlope(self, self.listKotaText, [self.prvniBodKotyCoord, self.vektorFin])
                    if context.scene.DIMENSION.dimType == 'Slope no overlap':
                        dimSlopeNo.osadKotuSlopeNo(self, self.listKotaText, [self.prvniBodKotyCoord, self.vektorFin])
                    if context.scene.DIMENSION.dimType == 'Arrow in':
                        dimArrowIn.osadKotuArrowIn(self, self.listKotaText, [self.prvniBodKotyCoord, self.vektorFin])
                    if context.scene.DIMENSION.dimType == 'Arrow open':
                        dimArrowOpen.osadKotuArrowOpen(self, self.listKotaText, [self.prvniBodKotyCoord, self.vektorFin])
                    if context.scene.DIMENSION.dimType == 'Arrow out':
                        dimArrowOut.osadKotuArrowOut(self, self.listKotaText, [self.prvniBodKotyCoord, self.vektorFin])
                    
                    if self.debug == True:
                        self.timeItStop = timer()
                        print('Time before srovnejRotationEulerObjektum je ' + str((self.timeItStop - self.timeItStart)*1000))

                else:
                    #self.vytvorKotu1([self.vektorFin, self.prvniBodKotyCoord])
                    if context.scene.DIMENSION.dimType == 'Slope':
                        dimSlope.osadKotuSlope(self, self.listKotaText, [self.vektorFin, self.prvniBodKotyCoord])
                    if context.scene.DIMENSION.dimType == 'Slope no overlap':
                        dimSlopeNo.osadKotuSlopeNo(self, self.listKotaText, [self.vektorFin, self.prvniBodKotyCoord])
                    if context.scene.DIMENSION.dimType == 'Arrow in':
                        dimArrowIn.osadKotuArrowIn(self, self.listKotaText, [self.vektorFin, self.prvniBodKotyCoord])
                    if context.scene.DIMENSION.dimType == 'Arrow open':
                        dimArrowOpen.osadKotuArrowOpen(self, self.listKotaText, [self.vektorFin, self.prvniBodKotyCoord])
                    if context.scene.DIMENSION.dimType == 'Arrow out':
                        dimArrowOut.osadKotuArrowOut(self, self.listKotaText, [self.vektorFin, self.prvniBodKotyCoord])

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
                
                planeNormal = functions.planeNormalZflatLined(self, bod1, bod2) #pro svislou Z se otoci do X-Y
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
                    vektorKoty = functions.smerovyVektor(bod2, bod1)
                    velikostOdsazeni = functions.vzdalenostMeziDvemaBody(bod2, bod1) * 100
                    self.ObjektFaceRayCast.data.vertices[0].co = functions.pripoctiNejOsa(bod1, vektorKoty, velikostOdsazeni) 
                    self.ObjektFaceRayCast.data.vertices[1].co = functions.pripoctiNejOsa(bod2, vektorKoty, -velikostOdsazeni) 
                    self.ObjektFaceRayCast.data.vertices[3].co = functions.odsad(bod1, vektorKoty, 2, velikostOdsazeni)
                    self.ObjektFaceRayCast.data.vertices[2].co = functions.odsad(bod2, vektorKoty, 2, velikostOdsazeni)
                    return {'RUNNING_MODAL'}

                if self.delkaManualFloat > 0:
                    self.odsazZakl = self.delkaManualFloat

                if context.scene.DIMENSION.dimType == 'Slope':
                    if self.mouseMoved == True:
                        dimSlope.osadKotuSlope(self, self.listKotaText, [bod1, bod2, self.odsazZakl, self.posunKolecka])
                    else:
                        dimSlope.osadKotuSlope(self, self.listKotaText, [bod1, bod2])
                if context.scene.DIMENSION.dimType == 'Slope no overlap':
                    if self.mouseMoved == True:
                        dimSlopeNo.osadKotuSlopeNo(self, self.listKotaText, [bod1, bod2, self.odsazZakl, self.posunKolecka])
                    else:
                        dimSlopeNo.osadKotuSlopeNo(self, self.listKotaText, [bod1, bod2])
                if context.scene.DIMENSION.dimType == 'Arrow in':
                    if self.mouseMoved == True:
                        dimArrowIn.osadKotuArrowIn(self, self.listKotaText, [bod1, bod2, self.odsazZakl, self.posunKolecka])
                    else:
                        dimArrowIn.osadKotuArrowIn(self, self.listKotaText, [bod1, bod2])
                if context.scene.DIMENSION.dimType == 'Arrow open':
                    if self.mouseMoved == True:
                        dimArrowOpen.osadKotuArrowOpen(self, self.listKotaText, [bod1, bod2, self.odsazZakl, self.posunKolecka])
                    else:
                        dimArrowOpen.osadKotuArrowOpen(self, self.listKotaText, [bod1, bod2])
                if context.scene.DIMENSION.dimType == 'Arrow out':
                    if self.mouseMoved == True:
                        dimArrowOut.osadKotuArrowOut(self, self.listKotaText, [bod1, bod2, self.odsazZakl, self.posunKolecka])
                    else:
                        dimArrowOut.osadKotuArrowOut(self, self.listKotaText, [bod1, bod2])

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
                #bpy.ops.object.select_all(action='DESELECT')
                for obj in context.scene.objects:
                    obj.select_set(False)
                self.listKotaText[0].select_set(True)
                #activ je mesh a jeste mazeme mesh z activ, empty a text
                meshTmp = self.listKotaText[0].data
                #self.ObjektKoty.select_set(True) je selected v teto fazi
                #bpy.ops.object.delete() 
                bpy.data.objects.remove(self.listKotaText[0])
                bpy.data.meshes.remove(meshTmp)

                #delete TEXT
                #bpy.ops.object.select_all(action='DESELECT')
                for obj in context.scene.objects:
                    obj.select_set(False)
                curveTmp = self.listKotaText[1].data
                #self.listKotaText[1].select_set(True)
                #bpy.ops.object.delete() 
                bpy.data.objects.remove(self.listKotaText[1])
                bpy.data.curves.remove(curveTmp)
                #delete empty
                #self.objektFirsPoint.select_set(True)
                #bpy.ops.object.delete()

                #delete raycast plane
                if self.ObjektFaceRayCast != None:
                    #self.ObjektFaceRayCast.select_set(True)
                    meshTmp = self.ObjektFaceRayCast.data
                    #bpy.ops.object.delete() 
                    bpy.data.objects.remove(self.ObjektFaceRayCast)
                    bpy.data.meshes.remove(meshTmp)
                    ObjektFaceRayCast = None

            #bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')

            bpy.types.SpaceView3D.draw_handler_remove(self.nevimHandle, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self.nevimHandle2, 'WINDOW')

            return {'FINISHED'}
        
        if (event.type == 'LEFTMOUSE' and event.value == 'RELEASE') or (event.type == 'NUMPAD_ENTER' and event.value == 'RELEASE') or (event.type == 'RET' and event.value == 'RELEASE'):

            self.mouseLocation = event.mouse_region_x, event.mouse_region_y

            if self.currentState == 2:

                #bpy.ops.object.select_all(action='DESELECT')
                for obj in context.scene.objects:
                    obj.select_set(False)
                #self.listKotaText[0].select_set(True)
                #activ je mesh a jeste mazeme mesh z activ, empty a text
                meshTmp = self.listKotaText[0].data
                #self.ObjektKoty.select_set(True) je selected v teto fazi
                #bpy.ops.object.delete() 
                bpy.data.objects.remove(self.listKotaText[0])
                bpy.data.meshes.remove(meshTmp)

                #delete TEXT
                #bpy.ops.object.select_all(action='DESELECT')
                for obj in context.scene.objects:
                    obj.select_set(False)
                curveTmp = self.listKotaText[1].data
                #self.listKotaText[1].select_set(True)
                #bpy.ops.object.delete() 
                bpy.data.objects.remove(self.listKotaText[1])
                bpy.data.curves.remove(curveTmp)

                #delete raycast plane
                #self.ObjektFaceRayCast.select_set(True)
                meshTmp = self.ObjektFaceRayCast.data
                #bpy.ops.object.delete() 
                bpy.data.objects.remove(self.ObjektFaceRayCast)
                bpy.data.meshes.remove(meshTmp)
                self.ObjektFaceRayCast = None

                if self.mouseMoved == True: #possible jeden call
                    if context.scene.DIMENSION.dimType == 'Slope':
                        bpy.ops.mesh.dimension_two_vert('INVOKE_DEFAULT', True, boolFromModal = True, bod1 = self.prvniBodKotyCoord.copy(), bod2 = self.druhyBodKotyCoord.copy(), mouseMoved = self.mouseMoved, odsazeniHlavni = self.odsazZakl, odsazeniZakladna = self.posunKolecka, realtimeFinalDraw = True, otocit = self.otocit, boolFirstRun = True)
                    if context.scene.DIMENSION.dimType == 'Slope no overlap':
                        bpy.ops.mesh.dimension_two_vert('INVOKE_DEFAULT', True, boolFromModal = True, bod1 = self.prvniBodKotyCoord.copy(), bod2 = self.druhyBodKotyCoord.copy(), mouseMoved = self.mouseMoved, odsazeniHlavni = self.odsazZakl, odsazeniZakladna = self.posunKolecka, realtimeFinalDraw = True, otocit = self.otocit, boolFirstRun = True)
                    if context.scene.DIMENSION.dimType == 'Arrow out':
                        bpy.ops.mesh.dimension_two_vert('INVOKE_DEFAULT', True, boolFromModal = True, bod1 = self.prvniBodKotyCoord.copy(), bod2 = self.druhyBodKotyCoord.copy(), mouseMoved = self.mouseMoved, odsazeniHlavni = self.odsazZakl, odsazeniZakladna = self.posunKolecka, realtimeFinalDraw = True, otocit = self.otocit, boolFirstRun = True)
                    if context.scene.DIMENSION.dimType == 'Arrow in':
                        bpy.ops.mesh.dimension_two_vert('INVOKE_DEFAULT', True, boolFromModal = True, bod1 = self.prvniBodKotyCoord.copy(), bod2 = self.druhyBodKotyCoord.copy(), mouseMoved = self.mouseMoved, odsazeniHlavni = self.odsazZakl, odsazeniZakladna = self.posunKolecka, realtimeFinalDraw = True, otocit = self.otocit, boolFirstRun = True)
                    if context.scene.DIMENSION.dimType == 'Arrow open':
                        bpy.ops.mesh.dimension_two_vert('INVOKE_DEFAULT', True, boolFromModal = True, bod1 = self.prvniBodKotyCoord.copy(), bod2 = self.druhyBodKotyCoord.copy(), mouseMoved = self.mouseMoved, odsazeniHlavni = self.odsazZakl, odsazeniZakladna = self.posunKolecka, realtimeFinalDraw = True, otocit = self.otocit, boolFirstRun = True)
                else:
                    if context.scene.DIMENSION.dimType == 'Slope':
                        bpy.ops.mesh.dimension_two_vert('INVOKE_DEFAULT', True, boolFromModal = True, bod1 = self.prvniBodKotyCoord.copy(), bod2 = self.druhyBodKotyCoord.copy(), mouseMoved = self.mouseMoved, realtimeFinalDraw = True, otocit = self.otocit, boolFirstRun = True, continueMode = self.continueMode)
                    if context.scene.DIMENSION.dimType == 'Slope no overlap':
                        bpy.ops.mesh.dimension_two_vert('INVOKE_DEFAULT', True, boolFromModal = True, bod1 = self.prvniBodKotyCoord.copy(), bod2 = self.druhyBodKotyCoord.copy(), mouseMoved = self.mouseMoved, realtimeFinalDraw = True, otocit = self.otocit, boolFirstRun = True, continueMode = self.continueMode)
                    if context.scene.DIMENSION.dimType == 'Arrow out':
                        bpy.ops.mesh.dimension_two_vert('INVOKE_DEFAULT', True, boolFromModal = True, bod1 = self.prvniBodKotyCoord.copy(), bod2 = self.druhyBodKotyCoord.copy(), mouseMoved = self.mouseMoved, realtimeFinalDraw = True, otocit = self.otocit, boolFirstRun = True, continueMode = self.continueMode)
                    if context.scene.DIMENSION.dimType == 'Arrow in':
                        bpy.ops.mesh.dimension_two_vert('INVOKE_DEFAULT', True, boolFromModal = True, bod1 = self.prvniBodKotyCoord.copy(), bod2 = self.druhyBodKotyCoord.copy(), mouseMoved = self.mouseMoved, realtimeFinalDraw = True, otocit = self.otocit, boolFirstRun = True, continueMode = self.continueMode)
                    if context.scene.DIMENSION.dimType == 'Arrow open':
                        bpy.ops.mesh.dimension_two_vert('INVOKE_DEFAULT', True, boolFromModal = True, bod1 = self.prvniBodKotyCoord.copy(), bod2 = self.druhyBodKotyCoord.copy(), mouseMoved = self.mouseMoved, realtimeFinalDraw = True, otocit = self.otocit, boolFirstRun = True, continueMode = self.continueMode)

                #bpy.types.SpaceView3D.draw_handler_remove(self.nevimHandle, 'WINDOW')
                #bpy.types.SpaceView3D.draw_handler_remove(self.nevimHandle2, 'WINDOW')

                #pokud self.continueMode = True, tak jedeme dal else: finished
                if self.continueMode == True:
                    self.prvniBodKotyCoord = self.druhyBodKotyCoord
                    if context.scene.DIMENSION.dimType == 'Slope':
                        self.listKotaText = dimSlope.vytvorKotuSlope(self)
                    if context.scene.DIMENSION.dimType == 'Slope no overlap':
                        self.listKotaText = dimSlopeNo.vytvorKotuSlopeNo(self)
                    if context.scene.DIMENSION.dimType == 'Arrow out':
                        self.listKotaText = dimArrowOut.vytvorKotuArrowOut(self)
                    if context.scene.DIMENSION.dimType == 'Arrow in':
                        self.listKotaText = dimArrowIn.vytvorKotuArrowIn(self)
                    if context.scene.DIMENSION.dimType == 'Arrow open':
                        self.listKotaText = dimArrowOpen.vytvorKotuArrowOpen(self)
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
                #bpy.ops.mesh.primitive_plane_add()
                #test
                # Vytvoření nového Mesh objektu
                ObjektFaceRayCastMesh = bpy.data.meshes.new(name="raycastface")
                self.ObjektFaceRayCast = bpy.data.objects.new(name="dimension", object_data=ObjektFaceRayCastMesh)

                # Přidání do aktivní kolekce 
                bpy.context.collection.objects.link(self.ObjektFaceRayCast)

                # Vytvoření bmesh geometrie (rovina 2x2 Blender jednotky)
                bm = bmesh.new()
                bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=2.0)
                bm.to_mesh(ObjektFaceRayCastMesh)
                bm.free()  # Uvolnění paměti

                #here maybe set ObjektFaceRayCastMesh as active?


                #self.ObjektFaceRayCast = context.active_object
                self.ObjektFaceRayCast.hide_set(True)
                #ObjektFaceRayCastMesh = self.ObjektFaceRayCast.data
                if self.otocit == False:
                    vektorKoty = functions.smerovyVektor(self.prvniBodKotyCoord, self.druhyBodKotyCoord)
                    velikostOdsazeni = functions.vzdalenostMeziDvemaBody(self.prvniBodKotyCoord, self.druhyBodKotyCoord) * 100

                    ObjektFaceRayCastMesh.vertices[0].co = functions.pripoctiNejOsa(self.prvniBodKotyCoord, vektorKoty, velikostOdsazeni) 
                    ObjektFaceRayCastMesh.vertices[1].co = functions.pripoctiNejOsa(self.druhyBodKotyCoord, vektorKoty, -velikostOdsazeni) 
                    ObjektFaceRayCastMesh.vertices[3].co = functions.odsad(self.prvniBodKotyCoord, vektorKoty, 2, velikostOdsazeni)
                    ObjektFaceRayCastMesh.vertices[2].co = functions.odsad(self.druhyBodKotyCoord, vektorKoty, 2, velikostOdsazeni)
                else:
                    vektorKoty = functions.smerovyVektor(self.druhyBodKotyCoord, self.prvniBodKotyCoord)
                    velikostOdsazeni = functions.vzdalenostMeziDvemaBody(self.druhyBodKotyCoord, self.prvniBodKotyCoord) * 100

                    ObjektFaceRayCastMesh.vertices[0].co = functions.pripoctiNejOsa(self.prvniBodKotyCoord, vektorKoty, velikostOdsazeni) 
                    ObjektFaceRayCastMesh.vertices[1].co = functions.pripoctiNejOsa(self.druhyBodKotyCoord, vektorKoty, -velikostOdsazeni) 
                    ObjektFaceRayCastMesh.vertices[3].co = functions.odsad(self.prvniBodKotyCoord, vektorKoty, 2, velikostOdsazeni)
                    ObjektFaceRayCastMesh.vertices[2].co = functions.odsad(self.druhyBodKotyCoord, vektorKoty, 2, velikostOdsazeni)
                self.edgesMiddleText = 'active'
                if context.scene.DIMENSION.ignoreMid == True:
                    self.edgesMiddleText = 'turned off'
                self.textToDraw = 'move bottom lines with mouse scroll | specify distance from base with mouse, or directly with number keys | snaping to edges middle is ' + self.edgesMiddleText + ' - switch with M | continue mode is ' + self.continueModeText + ' - switch with C'

            self.continueModeHelpBool = False

            #tady jdeme vytvorit kotu (prvni bod na mysi)
            if self.currentState == 0:
                self.prvniBodKotyCoord = self.snap3Dfin.copy()
                if context.scene.DIMENSION.dimType == 'Slope':
                    self.listKotaText = dimSlope.vytvorKotuSlope(self)
                if context.scene.DIMENSION.dimType == 'Slope no overlap':
                    self.listKotaText = dimSlopeNo.vytvorKotuSlopeNo(self)
                if context.scene.DIMENSION.dimType == 'Arrow out':
                    self.listKotaText = dimArrowOut.vytvorKotuArrowOut(self)
                if context.scene.DIMENSION.dimType == 'Arrow in':
                    self.listKotaText = dimArrowIn.vytvorKotuArrowIn(self)
                if context.scene.DIMENSION.dimType == 'Arrow open':
                    self.listKotaText = dimArrowOpen.vytvorKotuArrowOpen(self)

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

        text = "Dimensions are by default aligned to X-Y plane - invisible from sides - please use Top view, or any other arbitrary angle. If you need side or front view, just copy and rotate what you are dimensioning. I will maybe add this functionality in future."
        if shortR[0] == 0.7071067690849304 and shortR[1] == 0.7071067690849304 and shortR[2] == 0.0 and shortR[3] == 0.0:
            self.report({'ERROR'}, text)
            return {'FINISHED'}
        if shortR[0] == 0.0 and shortR[1] == 0.0 and shortR[2] == 0.7071068286895752 and shortR[3] == 0.7071068286895752:
            self.report({'ERROR'}, text)
            return {'FINISHED'}
        if shortR[0] == 0.5 and shortR[1] == 0.5 and shortR[2] == 0.5 and shortR[3] == 0.5:
            self.report({'ERROR'}, text)
            return {'FINISHED'}
        if shortR[0] == 0.5 and shortR[1] == 0.5 and shortR[2] == -0.5 and shortR[3] == -0.5:
            self.report({'ERROR'}, text)
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
        return
    
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
        return
    
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
        return