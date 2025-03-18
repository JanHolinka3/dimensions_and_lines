import bpy #type:ignore
import bmesh #type:ignore
import math
import mathutils #type:ignore
from . import functions

class MESH_OT_hatches(bpy.types.Operator):
    """Create hatch"""
    bl_idname = "mesh.hatches"
    bl_label = "Hatches"
    bl_options = {'REGISTER', 'UNDO'}

    tloustka: bpy.props.FloatProperty(name="thickness",description="line thickness",default=0.1,min = 0,step=1, precision= 3) # type: ignore
    linesDistance: bpy.props.FloatProperty(name="lines distance", description="space between lines", default=0.3, min = 0.001, step=1, precision= 3) # type: ignore
    dashSpace: bpy.props.FloatProperty(name="gaps length", description="gaps length", default=0.3, min = 0.001, step=1, precision= 3) # type: ignore
    dashLine: bpy.props.FloatProperty(name="lines length", description="dash lines length", default=1.2, min = 0, step=1, precision= 3) # type: ignore
    dotSize: bpy.props.FloatProperty(name="dot size", description="do size length", default=0.1, min = 0, step=1, precision= 3) # type: ignore
    angle: bpy.props.IntProperty(name="angle", description="angle of hatch", default=0, min = -90, max = 90) # type: ignore
    boolFirstRun: bpy.props.BoolProperty(name="firstRun", description="determine if it is called from UI", default=False, options={'HIDDEN'}) # type: ignore
    #typ: bpy.props.IntProperty(name="type",description="type of line",default=0,min = 0,max = 3,)
    
    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'
    
    def execute(self, context):

        #print('new hatch')

        if bpy.context.active_object.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.ed.undo_push()
            bpy.ops.object.mode_set(mode='EDIT')

        bpy.ops.ed.undo_push()

        #kontrola poctu a typu objektu, selected visible edges...
        countObjektu = 0
        selectedObject = None
        for object in context.selected_objects:
            countObjektu = countObjektu + 1
            selectedObject = object

        if countObjektu == 0:
            self.report({'ERROR'}, "No object selected")
            return {'CANCELLED'}
        
        if countObjektu > 1:
            self.report({'ERROR'}, "Too many objects selected, select only one object.")
            return {'CANCELLED'}

        if selectedObject.type != 'MESH':
            self.report({'ERROR'}, "Selected object is not mesh.")
            return {'CANCELLED'}

        if context.scene.DIMENSION.ignoreUndo == True:
            if self.boolFirstRun == True:
                self.tloustka = 0.00014*context.scene.DIMENSION.scale #vychozi jako thin
                self.dashSpace = 7 * self.tloustka
                self.linesDistance = 7 * self.tloustka
                self.dashLine = 12 * self.tloustka
                self.dotSize = 1 * self.tloustka
                self.boolFirstRun = False
        self.dotSize = 1 * self.tloustka

        objectO = bpy.context.active_object

        switchBack = False
        if bpy.context.active_object.mode == 'EDIT':
            switchBack = True
            bpy.ops.object.mode_set(mode='OBJECT')

        bFAO=bmesh.new() 
        bFAO.from_mesh(objectO.data)  
        edgesList = []
        for edges in bFAO.edges:
            if edges.select == True:
                edgesList.append(edges) #mame list selected edges
        
        #kontrola selected visible edges...
        #mensi nebo rovno 2 znamena malo
        if len(edgesList) <= 2:
            self.report({'ERROR'}, "Too little edges. You need to select min. 3 edges and they should create closed area.")
            bFAO.free()
            if switchBack == True:
                bpy.ops.object.mode_set(mode='EDIT')
            return {'CANCELLED'}

        #uzavrene obasti a Z aligned _ loopnout edges a pro kazdy vert edge loopnot connected edges a min 2 musi byt v listu, jinak nejde o uzavrenou oblast
        firstLocation = False
        closeAreas = True
        kontrolaFin = False
        ZlocList = []
        Zloc = 0.0
        for edge in edgesList:
            pocetLinknutych = 0
            for eee in edge.verts[0].link_edges:
                if eee in edgesList:
                    pocetLinknutych += 1
            if pocetLinknutych < 2:
                closeAreas = False
            pocetLinknutych = 0
            for eee in edge.verts[1].link_edges:
                if eee in edgesList:
                    pocetLinknutych += 1
            if pocetLinknutych < 2:
                closeAreas = False
            # Z aligned
            if firstLocation == False:
                Zloc = edge.verts[0].co[2]
            firstLocation = True
            ZlocList.append(edge.verts[0].co[2])
            ZlocList.append(edge.verts[1].co[2])
            if kontrolaFin == False:
                if math.isclose(edge.verts[0].co[2], Zloc,abs_tol=0.00001) == False:
                    kontrolaFin = True
                    self.report({'WARNING'}, "Edges in selected area are not flatten out/aligned to object X-Y plane. Created hatches are flattened/aligned to object X-Y plane. To achieve different angle, please rotate the whole object.")
                if math.isclose(edge.verts[1].co[2], Zloc,abs_tol=0.00001) == False:
                    kontrolaFin = True
                    self.report({'WARNING'}, "Edges in selected area are not flatten out/aligned to object X-Y plane. Created hatches are flattened/aligned to object X-Y plane. To achieve different angle, please rotate the whole object.")

        if closeAreas == False:
            self.report({'ERROR'}, "It seams, that selected edges are not creating closed area.")
            if switchBack == True:
                bpy.ops.object.mode_set(mode='EDIT') 
            bFAO.free()
            return {'CANCELLED'}
        
        bpy.ops.mesh.primitive_plane_add()
        objectHatch = bpy.context.active_object
        objectHatch.location = objectO.location
        objectHatch.rotation_euler = objectO.rotation_euler
        objectHatch.scale = objectO.scale
        objectHatch.active_material = objectO.active_material

        bFA=bmesh.new()   
        bFA.from_mesh(objectHatch.data)  
        for vert in bFA.verts:
            bFA.verts.remove(vert)
        bFA.verts.ensure_lookup_table()



        if kontrolaFin == True:
            Zloc = sum(ZlocList) / len(ZlocList)

        #x_max, x_min, y_max, y_min
        boundingBoxList = functions.vratBoundingProEdges(edgesList)

        maxLenghtForCuts = abs(boundingBoxList[0] - boundingBoxList[1]) + abs(boundingBoxList[2] - boundingBoxList[3])

        odkotovanaVzdalenost = 0

        #tady pridavame edges - reseno jako prime cary u Lines, Lines dashed a Dots - cpeme do listEdgeNew
        if context.scene.DIMENSION.hatchesTypes == 'Lines' or context.scene.DIMENSION.hatchesTypes == 'Lines dashed' or context.scene.DIMENSION.hatchesTypes == 'Dots':
            Pripocet = 0
            edX1 = 0.0
            edY1 = 0.0
            listEdgeNew = []
            listVertToHide = []
            while odkotovanaVzdalenost < maxLenghtForCuts: #dokud neprojdeme pres boundingBox max X
                #tvorba prostrelovaciho edge - zavisle na bounding boxu - zacnu vlevo nahore - [1][2], pak svisle je [1][3]
                if self.angle >= 0 and self.angle <= 45:
                    Pripocet = odkotovanaVzdalenost * (1/math.cos(math.radians(self.angle)))
                    edX1 = boundingBoxList[1] + Pripocet
                    edY1 = boundingBoxList[2]
                if self.angle > 45 and self.angle <= 90:
                    Pripocet = odkotovanaVzdalenost * (1/math.sin(math.radians(self.angle)))
                    edX1 = boundingBoxList[0] 
                    edY1 = boundingBoxList[3] + Pripocet
                if self.angle < 0 and self.angle >= -45:
                    Pripocet = - odkotovanaVzdalenost * (1/math.cos(math.radians(self.angle)))
                    edX1 = boundingBoxList[0] + Pripocet
                    edY1 = boundingBoxList[2]
                if self.angle < -45 and self.angle >= -90:
                    Pripocet = - odkotovanaVzdalenost * (1/math.sin(math.radians(self.angle)))
                    edX1 = boundingBoxList[1] 
                    edY1 = boundingBoxList[3] + Pripocet
                edX2 = edX1 + (math.sin(math.radians(self.angle)) * 1)
                edY2 = edY1 + (math.cos(math.radians(self.angle)) * 1)
                edgeCut = (edX1, edY1, edX2, edY2)

                odkotovanaVzdalenost = odkotovanaVzdalenost + self.linesDistance

                seznamBodu = functions.vratStycneBody(edgesList, edgeCut, Zloc) #stycne body uz jdou od nejmensiho k nejvetsimu

                prvni = False
                druhy = False
                bod1 = None
                bod2 = None
                for bod in seznamBodu:
                    if prvni == False:
                        bod1 = bFA.verts.new(bod)
                        prvni = True
                        druhy = False
                        listVertToHide.append(bod1)
                    else:
                        bod2 = bFA.verts.new(bod)
                        prvni = False
                        druhy = True
                        listVertToHide.append(bod2)

                    if druhy == True:
                        if bod1.co[0] != bod2.co[0] or bod1.co[1] != bod2.co[1]:
                            edge1 = bFA.edges.new((bod1,bod2))
                            listEdgeNew.append(edge1)
                            druhy = False
                        else:
                            bod1.hide_set(True)
                            bod2.hide_set(True)

        if context.scene.DIMENSION.hatchesTypes == '3-1 Lines':
            Pripocet = 0
            edX1 = 0.0
            edY1 = 0.0
            listEdgeNew = []
            listVertToHide = []
            counter = 0
            while odkotovanaVzdalenost < maxLenghtForCuts: #dokud neprojdeme pres boundingBox max X
                counter += 1
                if counter > 3:
                    if counter > 3:
                        counter = 0
                    odkotovanaVzdalenost = odkotovanaVzdalenost + self.linesDistance
                    continue

                #tvorba prostrelovaciho edge - zavisle na bounding boxu - zacnu vlevo nahore - [1][2], pak svisle je [1][3]
                if self.angle >= 0 and self.angle <= 45:
                    Pripocet = odkotovanaVzdalenost * (1/math.cos(math.radians(self.angle)))
                    edX1 = boundingBoxList[1] + Pripocet
                    edY1 = boundingBoxList[2]
                if self.angle > 45 and self.angle <= 90:
                    Pripocet = odkotovanaVzdalenost * (1/math.sin(math.radians(self.angle)))
                    edX1 = boundingBoxList[0] 
                    edY1 = boundingBoxList[3] + Pripocet
                if self.angle < 0 and self.angle >= -45:
                    Pripocet = - odkotovanaVzdalenost * (1/math.cos(math.radians(self.angle)))
                    edX1 = boundingBoxList[0] + Pripocet
                    edY1 = boundingBoxList[2]
                if self.angle < -45 and self.angle >= -90:
                    Pripocet = - odkotovanaVzdalenost * (1/math.sin(math.radians(self.angle)))
                    edX1 = boundingBoxList[1] 
                    edY1 = boundingBoxList[3] + Pripocet
                edX2 = edX1 + (math.sin(math.radians(self.angle)) * 1)
                edY2 = edY1 + (math.cos(math.radians(self.angle)) * 1)
                edgeCut = (edX1, edY1, edX2, edY2)

                odkotovanaVzdalenost = odkotovanaVzdalenost + self.linesDistance

                seznamBodu = functions.vratStycneBody(edgesList, edgeCut, Zloc) #stycne body uz jdou od nejmensiho k nejvetsimu

                prvni = False
                druhy = False
                bod1 = None
                bod2 = None
                for bod in seznamBodu:
                    if prvni == False:
                        bod1 = bFA.verts.new(bod)
                        prvni = True
                        druhy = False
                        listVertToHide.append(bod1)
                    else:
                        bod2 = bFA.verts.new(bod)
                        prvni = False
                        druhy = True
                        listVertToHide.append(bod2)

                    if druhy == True:
                        if bod1.co[0] != bod2.co[0] or bod1.co[1] != bod2.co[1]:
                            edge1 = bFA.edges.new((bod1,bod2))
                            listEdgeNew.append(edge1)
                            druhy = False
                        else:
                            bod1.hide_set(True)
                            bod2.hide_set(True)
           
        #tady pridavame edges - reseno jako prime cary z jedne a z druhe strany - cpeme do listEdgeNew
        if context.scene.DIMENSION.hatchesTypes == 'Grid':
            Pripocet = 0
            edX1 = 0.0
            edY1 = 0.0
            listEdgeNew = []
            listVertToHide = []
            while odkotovanaVzdalenost < maxLenghtForCuts: #dokud neprojdeme pres boundingBox max X
                #tvorba prostrelovaciho edge - zavisle na bounding boxu - zacnu vlevo nahore - [1][2], pak svisle je [1][3]
                if self.angle >= 0 and self.angle <= 45:
                    Pripocet = odkotovanaVzdalenost * (1/math.cos(math.radians(self.angle)))
                    edX1 = boundingBoxList[1] + Pripocet
                    edY1 = boundingBoxList[2]
                if self.angle > 45 and self.angle <= 90:
                    Pripocet = odkotovanaVzdalenost * (1/math.sin(math.radians(self.angle)))
                    edX1 = boundingBoxList[0] 
                    edY1 = boundingBoxList[3] + Pripocet
                if self.angle < 0 and self.angle >= -45:
                    Pripocet = - odkotovanaVzdalenost * (1/math.cos(math.radians(self.angle)))
                    edX1 = boundingBoxList[0] + Pripocet
                    edY1 = boundingBoxList[2]
                if self.angle < -45 and self.angle >= -90:
                    Pripocet = - odkotovanaVzdalenost * (1/math.sin(math.radians(self.angle)))
                    edX1 = boundingBoxList[1] 
                    edY1 = boundingBoxList[3] + Pripocet
                edX2 = edX1 - (math.sin(math.radians(self.angle)) * 1)
                edY2 = edY1 - (math.cos(math.radians(self.angle)) * 1)
                edgeCut = (edX1, edY1, edX2, edY2)

                odkotovanaVzdalenost = odkotovanaVzdalenost + self.linesDistance

                seznamBodu = functions.vratStycneBody(edgesList, edgeCut, Zloc) #stycne body uz jdou od nejmensiho k nejvetsimu

                prvni = False
                druhy = False
                bod1 = None
                bod2 = None
                for bod in seznamBodu:
                    if prvni == False:
                        bod1 = bFA.verts.new(bod)
                        prvni = True
                        druhy = False
                        listVertToHide.append(bod1)
                    else:
                        bod2 = bFA.verts.new(bod)
                        prvni = False
                        druhy = True
                        listVertToHide.append(bod2)

                    if druhy == True:
                        if bod1.co[0] != bod2.co[0] or bod1.co[1] != bod2.co[1]:
                            edge1 = bFA.edges.new((bod1,bod2))
                            listEdgeNew.append(edge1)
                            druhy = False
                        else:
                            bod1.hide_set(True)
                            bod2.hide_set(True)
            
            Pripocet = 0
            edX1 = 0.0
            edY1 = 0.0
            odkotovanaVzdalenost = 0
            while odkotovanaVzdalenost < maxLenghtForCuts: #dokud neprojdeme pres boundingBox max X
                #tvorba prostrelovaciho edge - zavisle na bounding boxu - zacnu vlevo nahore - [1][2], pak svisle je [1][3]
                if self.angle >= 0 and self.angle <= 45:
                    Pripocet = - odkotovanaVzdalenost * (1/math.cos(math.radians(self.angle)))
                    edX1 = boundingBoxList[0] 
                    edY1 = boundingBoxList[2] + Pripocet
                if self.angle > 45 and self.angle <= 90:
                    Pripocet = odkotovanaVzdalenost * (1/math.sin(math.radians(self.angle)))
                    edX1 = boundingBoxList[1] + Pripocet
                    edY1 = boundingBoxList[3] 
                if self.angle < 0 and self.angle >= -45:
                    Pripocet = odkotovanaVzdalenost * (1/math.cos(math.radians(self.angle)))
                    edX1 = boundingBoxList[0] 
                    edY1 = boundingBoxList[3] + Pripocet
                if self.angle < -45 and self.angle >= -90:
                    Pripocet = - odkotovanaVzdalenost * (1/math.sin(math.radians(self.angle)))
                    edX1 = boundingBoxList[1] + Pripocet
                    edY1 = boundingBoxList[2] 
                edX2 = edX1 - (math.sin(math.radians(self.angle + 90)) * 1)
                edY2 = edY1 - (math.cos(math.radians(self.angle + 90)) * 1)
                edgeCut = (edX1, edY1, edX2, edY2)

                odkotovanaVzdalenost = odkotovanaVzdalenost + self.linesDistance

                seznamBodu = functions.vratStycneBody(edgesList, edgeCut, Zloc) #stycne body uz jdou od nejmensiho k nejvetsimu

                prvni = False
                druhy = False
                bod1 = None
                bod2 = None
                for bod in seznamBodu:
                    if prvni == False:
                        bod1 = bFA.verts.new(bod)
                        prvni = True
                        druhy = False
                        listVertToHide.append(bod1)
                    else:
                        bod2 = bFA.verts.new(bod)
                        prvni = False
                        druhy = True
                        listVertToHide.append(bod2)

                    if druhy == True:
                        if bod1.co[0] != bod2.co[0] or bod1.co[1] != bod2.co[1]:
                            edge1 = bFA.edges.new((bod1,bod2))
                            listEdgeNew.append(edge1)
                            druhy = False
                        else:
                            bod1.hide_set(True)
                            bod2.hide_set(True)
        
        #pridavame tlousky na edges - podobne jako thicknes to edges
        if (context.scene.DIMENSION.hatchesTypes == 'Lines' or context.scene.DIMENSION.hatchesTypes == 'Grid' or context.scene.DIMENSION.hatchesTypes =='3-1 Lines'):
            listForBevel = []
            #pro kazdy edge mu budu davat tloustku - uplne stejne jako Lines - thicknes
            for edges in listEdgeNew:
                vertice1=edges.verts[0].co  #vytahnu jeho dve vert
                vertice2=edges.verts[1].co  
                smeroyVektor=functions.smerovyVektor(vertice1,vertice2) #vypocitam z nich smerovy vektor kvuli odsazovani na kolmici a primo
                #jedna strana 
                vertice3 = bFA.verts.new(functions.odsad(vertice1,smeroyVektor,2,self.tloustka/2)) 
                listForBevel.append(vertice3)
                vertice4 = bFA.verts.new(functions.odsad(vertice2,smeroyVektor,2,self.tloustka/2))
                listForBevel.append(vertice4)

                #vertice3.co = functions.pripoctiNejOsa(vertice3.co,smeroyVektor,-self.tloustka/2)
                #vertice4.co = functions.pripoctiNejOsa(vertice4.co,smeroyVektor,self.tloustka/2)

                #druha strana
                vertice5 = bFA.verts.new(functions.odsad(vertice1,smeroyVektor,2,-self.tloustka/2))
                listForBevel.append(vertice5)
                vertice6 = bFA.verts.new(functions.odsad(vertice2,smeroyVektor,2,-self.tloustka/2))
                listForBevel.append(vertice6)

                #vertice5.co = functions.pripoctiNejOsa(vertice5.co,smeroyVektor,-self.tloustka/2)
                #vertice6.co = functions.pripoctiNejOsa(vertice6.co,smeroyVektor,self.tloustka/2)

                bFA.faces.new([vertice4,vertice3,vertice5,vertice6])    

                vertice3.hide_set(True)
                vertice4.hide_set(True)
                vertice5.hide_set(True)
                vertice6.hide_set(True)

        #pridavame tlousky na edges - podobne jako thicknes to edges
        if (context.scene.DIMENSION.hatchesTypes == 'Lines dashed'):
            listForBevel = []

            #for edges in listEdgeNew: #pro kazdy edge
            edgesCount = len(listEdgeNew)
            for i in range(edgesCount):
                vertice1 = listEdgeNew[i].verts[0]  #vytahnu jeho dve vert
                vertice2 = listEdgeNew[i].verts[1] 
                smeroyVektor=functions.smerovyVektor(vertice1.co,vertice2.co) #vypocitam z nich smerovy vektor kvuli odsazovani na kolmici a primo
                #jedna strana
                vzdalenost = functions.vzdalenostMeziDvemaBody(vertice1.co, vertice2.co)
                paintedDist = 0

                firstRun = True
                #pridavat budu dokud nevycerpam vzdalenost 
                while paintedDist < vzdalenost:
                    #koncime kdyz by dalsi cara presahovala delku edge
                    if paintedDist + self.dashSpace > vzdalenost: break 

                    helpBoolOdsazeni = False
                    helpBoolZkracena = False
                    helpBoolOdsazeni2 = False
                    helpBoolZkracena2 = False
                    zbytek = 0.0

                    if firstRun == True and i > 0:#only on firstRun == True and az od druheho
                        bod3 = mathutils.Vector(listEdgeNew[0].verts[0].co)
                        bod4 = mathutils.Vector(listEdgeNew[0].verts[1].co)
                        bod2 = mathutils.Vector(functions.odsad(vertice1.co,smeroyVektor,2,1.0))
                        bod1 = mathutils.Vector(vertice1.co)
                        bodiky = mathutils.geometry.intersect_line_line(bod1, bod2, bod3, bod4)
                        #print(bodiky[0])

                        vzdalenost2 = functions.vzdalenostMeziDvemaBody(bod3, bodiky[0])#tohle bych mel osetrit jestli je nad nebo pod a podle toho pocitat zbytek.... x max a y max?
                        if i % 2 == 1:
                            vzdalenost2 = vzdalenost2 + ((self.dashLine + self.dashSpace)/2)

                        deleno = math.floor(vzdalenost2/(self.dashLine + self.dashSpace))

                        zbytek = vzdalenost2 - ((self.dashLine + self.dashSpace) * deleno)

                        if bodiky[0][0] > bod3[0] or bodiky[0][1] > bod3[1]:#jsme nad?
                            #print('nad')
                            if zbytek < self.dashSpace:
                                helpBoolOdsazeni = True
                                #pass#posouvam dolu o zbytek
                            if zbytek > self.dashSpace:
                                helpBoolZkracena = True
                                #pass#kreslim prvni line zkracenou na zbytek - self.dashSpace
                        else:
                            #print('pod')
                            #print(zbytek)
                            if zbytek < self.dashLine: #odsadime o self.dashSpace - zbytek
                                #print('odsazujeme')
                                helpBoolZkracena2 = True
                                #pass
                            if zbytek > self.dashLine:
                                #print('kreslime zbytek')
                                helpBoolOdsazeni2 = True
                                #pass#kreslime zbytek - space 
                    
                        
                    if firstRun == True:
                        paintedDist = paintedDist + self.tloustka/2
                        vertice3 = bFA.verts.new(functions.odsad(vertice1.co,smeroyVektor,2,self.tloustka/2)) #pri first run vytahujeme od krajni vert dva body a odsazujeme kolmo
                        listForBevel.append(vertice3)
                        vertice4 = bFA.verts.new(functions.odsad(vertice1.co,smeroyVektor,2,-self.tloustka/2))
                        listForBevel.append(vertice4)
                        if helpBoolOdsazeni == True:
                            #vertice3.co = functions.pripoctiNejOsa(vertice3.co,smeroyVektor,(-self.tloustka/2 + zbytek)) #odsadime po smeru cary zpet o polovinu tloustky cary
                            #vertice4.co = functions.pripoctiNejOsa(vertice4.co,smeroyVektor,(-self.tloustka/2 + zbytek))
                            vertice3.co = functions.pripoctiNejOsa(vertice3.co,smeroyVektor,(zbytek)) #odsadime po smeru cary zpet o polovinu tloustky cary
                            vertice4.co = functions.pripoctiNejOsa(vertice4.co,smeroyVektor,(zbytek))
                            paintedDist = paintedDist + zbytek
                        elif helpBoolOdsazeni2 == True:
                            #vertice3.co = functions.pripoctiNejOsa(vertice3.co,smeroyVektor,(-self.tloustka/2 + ((self.dashLine + self.dashSpace) - zbytek))) #odsadime po smeru cary zpet o polovinu tloustky cary
                            #vertice4.co = functions.pripoctiNejOsa(vertice4.co,smeroyVektor,(-self.tloustka/2 + ((self.dashLine + self.dashSpace) - zbytek)))
                            vertice3.co = functions.pripoctiNejOsa(vertice3.co,smeroyVektor,(((self.dashLine + self.dashSpace) - zbytek))) #odsadime po smeru cary zpet o polovinu tloustky cary
                            vertice4.co = functions.pripoctiNejOsa(vertice4.co,smeroyVektor,(((self.dashLine + self.dashSpace) - zbytek)))
                            paintedDist = paintedDist + ((self.dashLine + self.dashSpace) - zbytek)
                        else:
                            #vertice3.co = functions.pripoctiNejOsa(vertice3.co,smeroyVektor,(-self.tloustka/2)) #odsadime po smeru cary zpet o polovinu tloustky cary
                            #vertice4.co = functions.pripoctiNejOsa(vertice4.co,smeroyVektor,(-self.tloustka/2))
                            pass
                        firstRun = False
                    else:
                        vertice3 = bFA.verts.new(vertice5.co) #pri dalsich loops pridame dva body na posledni dva pridane
                        listForBevel.append(vertice3)
                        vertice4 = bFA.verts.new(vertice6.co)
                        listForBevel.append(vertice4)
                        vertice3.co = functions.pripoctiNejOsa(vertice3.co,smeroyVektor,self.dashSpace) #posunume je o mezeru po smeru
                        vertice4.co = functions.pripoctiNejOsa(vertice4.co,smeroyVektor,self.dashSpace)
                        paintedDist = paintedDist + self.dashSpace
                    #takzde ted sme pokazde na zacatku carky

                    #only on firstRun == True and jsem na druhem edge - koukam zpet
                    #teoreticky postup:testuju po vystreleni kolmice doprava (+) protnuni s nasledujici edge - v loopu - to mi asi vyjde vzdycky... zadny LOOP a TRUE
                    #TRUE - end loop a:
                    #vydelim vzdalenost od mista protnuti se vzdalenost (delka mezery + delka cary) a podle zbytku jsem schopny dopocitat kolik mam odsadit na prvnim vrcholu edge - 
                    # respektive if else pro odsadit o cast mezery nebo udelat umerne kratsi caru - zavisi i na tom jestli sem v loopu na zacatku, nebo jsem poskocil o caru nebo o mezeru!

                    # FALSE - continue loop 
                    # posunuju se o tloustku cary nebo mezeru a znova loop


                    vertice5 = bFA.verts.new(vertice3.co) #pridame druhe dve vert cary
                    listForBevel.append(vertice5)      
                    vertice6 = bFA.verts.new(vertice4.co)
                    listForBevel.append(vertice6)  

                    if helpBoolZkracena == True:
                        novaVzd = zbytek - self.dashSpace
                        if paintedDist + novaVzd > vzdalenost: #posunume o delku cary, popripade jenom o zbyvajici kus cary
                            vertice5.co = functions.pripoctiNejOsa(vertice5.co,smeroyVektor,vzdalenost - paintedDist + self.tloustka/2)
                            vertice6.co = functions.pripoctiNejOsa(vertice6.co,smeroyVektor,vzdalenost - paintedDist + self.tloustka/2)
                        else:
                            vertice5.co = functions.pripoctiNejOsa(vertice5.co,smeroyVektor,novaVzd)
                            vertice6.co = functions.pripoctiNejOsa(vertice6.co,smeroyVektor,novaVzd)
                    elif helpBoolZkracena2 == True:
                        if paintedDist + (self.dashLine - zbytek) > vzdalenost: #posunume o delku cary - zbytek
                            vertice5.co = functions.pripoctiNejOsa(vertice5.co,smeroyVektor,vzdalenost - paintedDist + self.tloustka/2)
                            vertice6.co = functions.pripoctiNejOsa(vertice6.co,smeroyVektor,vzdalenost - paintedDist + self.tloustka/2)
                        else:
                            vertice5.co = functions.pripoctiNejOsa(vertice5.co,smeroyVektor,(self.dashLine - zbytek))
                            vertice6.co = functions.pripoctiNejOsa(vertice6.co,smeroyVektor,(self.dashLine - zbytek))
                    else:
                        if paintedDist + self.dashLine > vzdalenost: #posunume o delku cary, popripade jenom o zbyvajici kus cary
                            vertice5.co = functions.pripoctiNejOsa(vertice5.co,smeroyVektor,vzdalenost - paintedDist + self.tloustka/2)
                            vertice6.co = functions.pripoctiNejOsa(vertice6.co,smeroyVektor,vzdalenost - paintedDist + self.tloustka/2)
                        else:
                            vertice5.co = functions.pripoctiNejOsa(vertice5.co,smeroyVektor,self.dashLine)
                            vertice6.co = functions.pripoctiNejOsa(vertice6.co,smeroyVektor,self.dashLine)

                    if helpBoolZkracena == True:
                        paintedDist = paintedDist + novaVzd #evidujeme uslou vzdalenost
                    elif helpBoolZkracena2 == True:
                        paintedDist = paintedDist + (self.dashLine - zbytek) #evidujeme uslou vzdalenost
                    else:
                        paintedDist = paintedDist + self.dashLine #evidujeme uslou vzdalenost

                    bFA.faces.new([vertice3, vertice4, vertice6, vertice5])

                    vertice3.hide_set(True)
                    vertice4.hide_set(True)
                    vertice5.hide_set(True)
                    vertice6.hide_set(True) 

        #pridavame tlousky na edges - podobne jako thicknes to edges
        if (context.scene.DIMENSION.hatchesTypes == 'Dots'):
            listForBevel = []

            edgesCount = len(listEdgeNew)
            #for edges in listEdgeNew: #pro kazdy edge
            for i in range(edgesCount):
                vertice1 = listEdgeNew[i].verts[0]  #vytahnu jeho dve vert
                vertice2 = listEdgeNew[i].verts[1] 
                smeroyVektor=functions.smerovyVektor(vertice1.co,vertice2.co) #vypocitam z nich smerovy vektor kvuli odsazovani na kolmici a primo
                #jedna strana
                vzdalenost = functions.vzdalenostMeziDvemaBody(vertice1.co, vertice2.co)
                paintedDist = 0

                firstRun = True
                #pridavat budu dokud nevycerpam vzdalenost 
                while paintedDist < vzdalenost:
                    #prvni dve tecky
                    if paintedDist + functions.dashSpace > vzdalenost: break 

                    helpBoolOdsazeni = False
                    helpBoolZkracena = False
                    helpBoolOdsazeni2 = False
                    helpBoolZkracena2 = False
                    zbytek = 0.0


                    if firstRun == True and i > 0:#only on firstRun == True and az od druheho
                        bod3 = mathutils.Vector(listEdgeNew[0].verts[0].co)
                        bod4 = mathutils.Vector(listEdgeNew[0].verts[1].co)
                        bod2 = mathutils.Vector(functions.odsad(vertice1.co,smeroyVektor,2,1.0))
                        bod1 = mathutils.Vector(vertice1.co)
                        bodiky = mathutils.geometry.intersect_line_line(bod1, bod2, bod3, bod4)
                        #print(bodiky[0])

                        vzdalenost2 = functions.vzdalenostMeziDvemaBody(bod3, bodiky[0])#tohle bych mel osetrit jestli je nad nebo pod a podle toho pocitat zbytek.... x max a y max?
                        if i % 2 == 1:
                            vzdalenost2 = vzdalenost2 + ((self.dotSize + self.dashSpace)/2)

                        deleno = math.floor(vzdalenost2/(self.dotSize + self.dashSpace))

                        zbytek = vzdalenost2 - ((self.dotSize + self.dashSpace) * deleno)

                        if bodiky[0][0] > bod3[0] or bodiky[0][1] > bod3[1]:#jsme nad?
                            #print('nad')
                            if zbytek < self.dashSpace:
                                helpBoolOdsazeni = True
                                #pass#posouvam dolu o zbytek
                            if zbytek > self.dashSpace:
                                helpBoolZkracena = True
                                #pass#kreslim prvni line zkracenou na zbytek - self.dashSpace
                        else:
                            #print('pod')
                            #print(zbytek)
                            if zbytek < self.dotSize: #odsadime o self.dashSpace - zbytek
                                #print('odsazujeme')
                                helpBoolZkracena2 = True
                                #pass
                            if zbytek > self.dotSize:
                                #print('kreslime zbytek')
                                helpBoolOdsazeni2 = True
                                #pass#kreslime zbytek - space 

                    if firstRun == True:
                        paintedDist = paintedDist + self.tloustka/2
                        vertice3 = bFA.verts.new(functions.odsad(vertice1.co,smeroyVektor,2,self.tloustka/2)) 
                        listForBevel.append(vertice3)
                        vertice4 = bFA.verts.new(functions.odsad(vertice1.co,smeroyVektor,2,-self.tloustka/2))
                        listForBevel.append(vertice4)
                        if helpBoolOdsazeni == True:
                            #vertice3.co = functions.pripoctiNejOsa(vertice3.co,smeroyVektor,(-self.tloustka/2 + zbytek)) #odsadime po smeru cary zpet o polovinu tloustky cary
                            #vertice4.co = functions.pripoctiNejOsa(vertice4.co,smeroyVektor,(-self.tloustka/2 + zbytek))
                            vertice3.co = functions.pripoctiNejOsa(vertice3.co,smeroyVektor,(zbytek)) #odsadime po smeru cary zpet o polovinu tloustky cary
                            vertice4.co = functions.pripoctiNejOsa(vertice4.co,smeroyVektor,(zbytek))
                            paintedDist = paintedDist + zbytek
                        elif helpBoolOdsazeni2 == True:
                            #vertice3.co = functions.pripoctiNejOsa(vertice3.co,smeroyVektor,(-self.tloustka/2 + ((self.dotSize + self.dashSpace) - zbytek))) #odsadime po smeru cary zpet o polovinu tloustky cary
                            #vertice4.co = functions.pripoctiNejOsa(vertice4.co,smeroyVektor,(-self.tloustka/2 + ((self.dotSize + self.dashSpace) - zbytek)))
                            vertice3.co = functions.pripoctiNejOsa(vertice3.co,smeroyVektor,(((self.dotSize + self.dashSpace) - zbytek))) #odsadime po smeru cary zpet o polovinu tloustky cary
                            vertice4.co = functions.pripoctiNejOsa(vertice4.co,smeroyVektor,(((self.dotSize + self.dashSpace) - zbytek)))
                            paintedDist = paintedDist + ((self.dotSize + self.dashSpace) - zbytek)
                        else:
                            #vertice3.co = functions.pripoctiNejOsa(vertice3.co,smeroyVektor,-self.tloustka/2)
                            #vertice4.co = functions.pripoctiNejOsa(vertice4.co,smeroyVektor,-self.tloustka/2)
                            pass
                        firstRun = False
                    else:
                        vertice3 = bFA.verts.new(vertice5.co)
                        listForBevel.append(vertice3)
                        vertice4 = bFA.verts.new(vertice6.co)
                        listForBevel.append(vertice4)
                        vertice3.co = functions.pripoctiNejOsa(vertice3.co,smeroyVektor,self.dashSpace)
                        vertice4.co = functions.pripoctiNejOsa(vertice4.co,smeroyVektor,self.dashSpace)
                        paintedDist = paintedDist + self.dashSpace

                    #takze ted sme pokazde na zacatku carky
                    vertice5 = bFA.verts.new(vertice3.co)  
                    listForBevel.append(vertice5)     
                    vertice6 = bFA.verts.new(vertice4.co)
                    listForBevel.append(vertice6)  

                    if helpBoolZkracena == True:
                        novaVzd = zbytek - self.dashSpace
                        if paintedDist + novaVzd > vzdalenost:
                            vertice5.co = functions.pripoctiNejOsa(vertice5.co,smeroyVektor,vzdalenost - paintedDist + self.tloustka/2)
                            vertice6.co = functions.pripoctiNejOsa(vertice6.co,smeroyVektor,vzdalenost - paintedDist + self.tloustka/2)
                        else:
                            vertice5.co = functions.pripoctiNejOsa(vertice5.co,smeroyVektor,novaVzd)
                            vertice6.co = functions.pripoctiNejOsa(vertice6.co,smeroyVektor,novaVzd)
                    elif helpBoolZkracena2 == True:
                        if paintedDist + (self.dotSize - zbytek) > vzdalenost: #posunume o delku cary - zbytek
                            vertice5.co = functions.pripoctiNejOsa(vertice5.co,smeroyVektor,vzdalenost - paintedDist + self.tloustka/2)
                            vertice6.co = functions.pripoctiNejOsa(vertice6.co,smeroyVektor,vzdalenost - paintedDist + self.tloustka/2)
                        else:
                            vertice5.co = functions.pripoctiNejOsa(vertice5.co,smeroyVektor,(self.dotSize - zbytek))
                            vertice6.co = functions.pripoctiNejOsa(vertice6.co,smeroyVektor,(self.dotSize - zbytek))
                    else:
                        if paintedDist + self.dotSize > vzdalenost: #posunume o delku cary, popripade jenom o zbyvajici kus cary
                            vertice5.co = functions.pripoctiNejOsa(vertice5.co,smeroyVektor,vzdalenost - paintedDist + self.tloustka/2)
                            vertice6.co = functions.pripoctiNejOsa(vertice6.co,smeroyVektor,vzdalenost - paintedDist + self.tloustka/2)
                        else:
                            vertice5.co = functions.pripoctiNejOsa(vertice5.co,smeroyVektor,self.dotSize)
                            vertice6.co = functions.pripoctiNejOsa(vertice6.co,smeroyVektor,self.dotSize)

                    if helpBoolZkracena == True:
                        paintedDist = paintedDist + novaVzd #evidujeme uslou vzdalenost
                    elif helpBoolZkracena2 == True:
                        paintedDist = paintedDist + (self.dotSize - zbytek) #evidujeme uslou vzdalenost
                    else:
                        paintedDist = paintedDist + self.dotSize #evidujeme uslou vzdalenost

                    #paintedDist = paintedDist + self.dotSize

                    bFA.faces.new([vertice3, vertice4, vertice6, vertice5])

                    vertice3.hide_set(True)
                    vertice4.hide_set(True)
                    vertice5.hide_set(True)
                    vertice6.hide_set(True)

        if (context.scene.DIMENSION.hatchesTypes == 'Dash-dotted'):
            listForBevel = []

            shortBool = False

            #for edges in listEdgeNew: #pro kazdy edge
            edgesCount = len(listEdgeNew)
            for i in range(edgesCount):
                vertice1 = listEdgeNew[i].verts[0]  #vytahnu jeho dve vert
                vertice2 = listEdgeNew[i].verts[1] 
                smeroyVektor=functions.smerovyVektor(vertice1.co,vertice2.co) #vypocitam z nich smerovy vektor kvuli odsazovani na kolmici a primo
                #jedna strana
                vzdalenostBase = functions.vzdalenostMeziDvemaBody(vertice1.co, vertice2.co)
                vzdalenost = vzdalenostBase

                paintedDist = 0

                firstRun = True
                shortBool = False #mozna poladit podle odsazeni nejak jeste..... protoze takhle vzdycky zaciname carkou
                #pridavat budu dokud nevycerpam vzdalenost 
                while paintedDist < vzdalenost:
                    #koncime kdyz by dalsi cara presahovala delku edge
                    if paintedDist + self.dashSpace > vzdalenost: break 

                    helpBoolOdsazeni = False
                    helpBoolZkracena = False
                    helpBoolOdsazeni2 = False
                    helpBoolZkracena2 = False
                    zbytek = 0.0

                    if firstRun == True and i > 0:#only on firstRun == True and az od druheho
                        bod3 = mathutils.Vector(listEdgeNew[0].verts[0].co)
                        bod4 = mathutils.Vector(listEdgeNew[0].verts[1].co)
                        bod2 = mathutils.Vector(functions.odsad(vertice1.co,smeroyVektor,2,1.0))
                        bod1 = mathutils.Vector(vertice1.co)
                        bodiky = mathutils.geometry.intersect_line_line(bod1, bod2, bod3, bod4)
                        #print(bodiky[0])

                        vzdalenost2 = functions.vzdalenostMeziDvemaBody(bod3, bodiky[0])#tohle bych mel osetrit jestli je nad nebo pod a podle toho pocitat zbytek.... x max a y max?
                        if i % 2 == 1:
                            vzdalenost2 = vzdalenost2 + ((self.dashLine + self.dashSpace)/2)

                        deleno = math.floor(vzdalenost2/(self.dashLine + self.dashSpace))

                        zbytek = vzdalenost2 - ((self.dashLine + self.dashSpace) * deleno)

                        if bodiky[0][0] > bod3[0] or bodiky[0][1] > bod3[1]:#jsme nad?
                            #print('nad')
                            if zbytek < self.dashSpace:
                                helpBoolOdsazeni = True
                                #pass#posouvam dolu o zbytek
                            if zbytek > self.dashSpace:
                                helpBoolZkracena = True
                                #pass#kreslim prvni line zkracenou na zbytek - self.dashSpace
                        else:
                            #print('pod')
                            #print(zbytek)
                            if zbytek < self.dashLine: #odsadime o self.dashSpace - zbytek
                                helpBoolZkracena2 = True
                                #pass
                            if zbytek > self.dashLine:
                                helpBoolOdsazeni2 = True
                                #pass#kreslime zbytek - space 
                    
                        
                    if firstRun == True:
                        paintedDist = paintedDist + self.tloustka/2
                        vertice3 = bFA.verts.new(functions.odsad(vertice1.co,smeroyVektor,2,self.tloustka/2)) #pri first run vytahujeme od krajni vert dva body a odsazujeme kolmo
                        listForBevel.append(vertice3)
                        vertice4 = bFA.verts.new(functions.odsad(vertice1.co,smeroyVektor,2,-self.tloustka/2))
                        listForBevel.append(vertice4)
                        if helpBoolOdsazeni == True:
                            #vertice3.co = functions.pripoctiNejOsa(vertice3.co,smeroyVektor,(-self.tloustka/2 + zbytek)) #odsadime po smeru cary zpet o polovinu tloustky cary
                            #vertice4.co = functions.pripoctiNejOsa(vertice4.co,smeroyVektor,(-self.tloustka/2 + zbytek))
                            vertice3.co = functions.pripoctiNejOsa(vertice3.co,smeroyVektor,(zbytek)) #odsadime po smeru cary zpet o polovinu tloustky cary
                            vertice4.co = functions.pripoctiNejOsa(vertice4.co,smeroyVektor,(zbytek))
                            paintedDist = paintedDist + zbytek
                        elif helpBoolOdsazeni2 == True:
                            #vertice3.co = functions.pripoctiNejOsa(vertice3.co,smeroyVektor,(-self.tloustka/2 + ((self.dashLine + self.dashSpace) - zbytek))) #odsadime po smeru cary zpet o polovinu tloustky cary
                            #vertice4.co = functions.pripoctiNejOsa(vertice4.co,smeroyVektor,(-self.tloustka/2 + ((self.dashLine + self.dashSpace) - zbytek)))
                            vertice3.co = functions.pripoctiNejOsa(vertice3.co,smeroyVektor,(((self.dashLine + self.dashSpace) - zbytek))) #odsadime po smeru cary zpet o polovinu tloustky cary
                            vertice4.co = functions.pripoctiNejOsa(vertice4.co,smeroyVektor,(((self.dashLine + self.dashSpace) - zbytek)))
                            paintedDist = paintedDist + ((self.dashLine + self.dashSpace) - zbytek)
                        else:
                            #vertice3.co = functions.pripoctiNejOsa(vertice3.co,smeroyVektor,(-self.tloustka/2)) #odsadime po smeru cary zpet o polovinu tloustky cary
                            #vertice4.co = functions.pripoctiNejOsa(vertice4.co,smeroyVektor,(-self.tloustka/2))
                            pass
                        firstRun = False
                    else:
                        vertice3 = bFA.verts.new(vertice5.co) #pri dalsich loops pridame dva body na posledni dva pridane
                        listForBevel.append(vertice3)
                        vertice4 = bFA.verts.new(vertice6.co)
                        listForBevel.append(vertice4)
                        vertice3.co = functions.pripoctiNejOsa(vertice3.co,smeroyVektor,self.dashSpace) #posunume je o mezeru po smeru
                        vertice4.co = functions.pripoctiNejOsa(vertice4.co,smeroyVektor,self.dashSpace)
                        paintedDist = paintedDist + self.dashSpace
                    #takzde ted sme pokazde na zacatku carky

                    #only on firstRun == True and jsem na druhem edge - koukam zpet
                    #teoreticky postup:testuju po vystreleni kolmice doprava (+) protnuni s nasledujici edge - v loopu - to mi asi vyjde vzdycky... zadny LOOP a TRUE
                    #TRUE - end loop a:
                    #vydelim vzdalenost od mista protnuti se vzdalenost (delka mezery + delka cary) a podle zbytku jsem schopny dopocitat kolik mam odsadit na prvnim vrcholu edge - 
                    # respektive if else pro odsadit o cast mezery nebo udelat umerne kratsi caru - zavisi i na tom jestli sem v loopu na zacatku, nebo jsem poskocil o caru nebo o mezeru!

                    # FALSE - continue loop 
                    # posunuju se o tloustku cary nebo mezeru a znova loop


                    vertice5 = bFA.verts.new(vertice3.co) #pridame druhe dve vert cary
                    listForBevel.append(vertice5)      
                    vertice6 = bFA.verts.new(vertice4.co)
                    listForBevel.append(vertice6)  

                    if helpBoolZkracena == True:
                        novaVzd = zbytek - self.dashSpace
                        if paintedDist + novaVzd > vzdalenost: #posunume o delku cary, popripade jenom o zbyvajici kus cary
                            vertice5.co = functions.pripoctiNejOsa(vertice5.co,smeroyVektor,vzdalenost - paintedDist + self.tloustka/2)
                            vertice6.co = functions.pripoctiNejOsa(vertice6.co,smeroyVektor,vzdalenost - paintedDist + self.tloustka/2)
                        else:
                            vertice5.co = functions.pripoctiNejOsa(vertice5.co,smeroyVektor,novaVzd)
                            vertice6.co = functions.pripoctiNejOsa(vertice6.co,smeroyVektor,novaVzd)
                    elif helpBoolZkracena2 == True:
                        if paintedDist + (self.dashLine - zbytek) > vzdalenost: #posunume o delku cary - zbytek
                            vertice5.co = functions.pripoctiNejOsa(vertice5.co,smeroyVektor,vzdalenost - paintedDist + self.tloustka/2)
                            vertice6.co = functions.pripoctiNejOsa(vertice6.co,smeroyVektor,vzdalenost - paintedDist + self.tloustka/2)
                        else:
                            vertice5.co = functions.pripoctiNejOsa(vertice5.co,smeroyVektor,(self.dashLine - zbytek))
                            vertice6.co = functions.pripoctiNejOsa(vertice6.co,smeroyVektor,(self.dashLine - zbytek))
                    else:
                        if paintedDist + self.dashLine > vzdalenost: #posunume o delku cary, popripade jenom o zbyvajici kus cary
                            vertice5.co = functions.pripoctiNejOsa(vertice5.co,smeroyVektor,vzdalenost - paintedDist + self.tloustka/2)
                            vertice6.co = functions.pripoctiNejOsa(vertice6.co,smeroyVektor,vzdalenost - paintedDist + self.tloustka/2)
                        else:
                            if shortBool == False:
                                vertice5.co = functions.pripoctiNejOsa(vertice5.co,smeroyVektor,self.dashLine)
                                vertice6.co = functions.pripoctiNejOsa(vertice6.co,smeroyVektor,self.dashLine)
                                shorBool = True
                            else:
                                vertice5.co = functions.pripoctiNejOsa(vertice5.co,smeroyVektor,self.tloustka)
                                vertice6.co = functions.pripoctiNejOsa(vertice6.co,smeroyVektor,self.tloustka)
                                shorBool = False

                    if helpBoolZkracena == True:
                        paintedDist = paintedDist + novaVzd #evidujeme uslou vzdalenost
                    elif helpBoolZkracena2 == True:
                        paintedDist = paintedDist + (self.dashLine - zbytek) #evidujeme uslou vzdalenost
                    else:
                        if shortBool == False:
                            paintedDist = paintedDist + self.tloustka #evidujeme uslou vzdalenost
                        else:
                            paintedDist = paintedDist + self.dashLine

                    bFA.faces.new([vertice3, vertice4, vertice6, vertice5])

                    vertice3.hide_set(True)
                    vertice4.hide_set(True)
                    vertice5.hide_set(True)
                    vertice6.hide_set(True) 

        #funkce pro kontrolu edgesListu - jestli ma vic jak dva koncove (vert visible jenom jedna, tak konec a error hlaska, jestli ma prave dva koncove, tak spojime a pridame do edge list a jestli je solo edge jeden, tak opet chyba a konec

        bmesh.ops.bevel(bFA, geom = listForBevel, offset=self.tloustka/3.5, affect='VERTICES',)
        
        #vymazeme listEdgeNew KPL
        bmesh.ops.delete(bFA, geom = listEdgeNew, context='EDGES')

        bFA.to_mesh(objectHatch.data)
        bFA.free() 
        bFAO.free()

        context.view_layer.objects.active = objectO
        objectHatch.select_set(True)
        objectO.select_set(True)
        bpy.ops.object.parent_set(type='OBJECT', xmirror=False, keep_transform=True)

        objNameBase = 'hatch.'
        objName = 'hatch'
        boolZapsano = False
        counter = 1 
        while boolZapsano == False:
            if bpy.data.objects.get(objName):
                #jmeno zabrano, pridavame + 1
                objName = objNameBase + str(counter)
                counter = counter + 1
            else:
                objectHatch.name = objName
                boolZapsano = True

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.mode_set(mode='OBJECT')

        objectHatch.select_set(False)
        objectO.select_set(False)

        return {'FINISHED'}
    
    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(self, "tloustka")
        row = layout.row()
        row.prop(self, "linesDistance")
        row = layout.row()
        row.prop(self, "angle")
        if context.scene.DIMENSION.hatchesTypes == 'Lines dashed':
            row = layout.row()
            row.prop(self, "dashLine")
            row = layout.row()
            row.prop(self, "dashSpace")
        if context.scene.DIMENSION.hatchesTypes == 'Dots':
            row = layout.row()
            row.prop(self, "dashSpace")

    