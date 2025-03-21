import bpy #type:ignore
import math
from . import functions

class MESH_OT_remake_dimension(bpy.types.Operator):
    """Remake dimension."""
    bl_idname = "mesh.remake_dimension"
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

            self.odsazeniHlavni = functions.vzdalenostMeziDvemaBody(meshKoty.vertices[0].co,meshKoty.vertices[48].co)
            self.odsazeniZakladna = functions.vzdalenostMeziDvemaBody(meshKoty.vertices[16].co,meshKoty.vertices[48].co)
            self.delkaSikmeCar = functions.vzdalenostMeziDvemaBody(meshKoty.vertices[29].co,meshKoty.vertices[28].co)
            self.tloustka = functions.vzdalenostMeziDvemaBody(meshKoty.vertices[17].co,meshKoty.vertices[18].co)
            self.presahKolmice = functions.vzdalenostMeziDvemaBody(meshKoty.vertices[0].co,meshKoty.vertices[22].co)
            self.protazeni = functions.vzdalenostMeziDvemaBody(meshKoty.vertices[0].co,meshKoty.vertices[2].co)
            self.rotace = int(math.degrees(objectKoty.rotation_euler[0]))
            typeTmp = 'Slope'
            testKonec = functions.indetifyText(self, context, objectTextu, objectKoty, meshKoty, typeTmp)
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

            self.odsazeniHlavni = functions.vzdalenostMeziDvemaBody(meshKoty.vertices[0].co,meshKoty.vertices[42].co)
            self.odsazeniZakladna = functions.vzdalenostMeziDvemaBody(meshKoty.vertices[12].co,meshKoty.vertices[42].co)
            self.delkaSikmeCar = functions.vzdalenostMeziDvemaBody(meshKoty.vertices[25].co,meshKoty.vertices[24].co)
            self.tloustka = functions.vzdalenostMeziDvemaBody(meshKoty.vertices[13].co,meshKoty.vertices[14].co)
            self.presahKolmice = functions.vzdalenostMeziDvemaBody(meshKoty.vertices[0].co,meshKoty.vertices[18].co)
            self.protazeni = functions.vzdalenostMeziDvemaBody(meshKoty.vertices[0].co,meshKoty.vertices[18].co)
            self.rotace = int(math.degrees(objectKoty.rotation_euler[0]))
            typeTmp = 'Slope no overlap'
            testKonec = functions.indetifyText(self, context, objectTextu, objectKoty, meshKoty, typeTmp)
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

                self.odsazeniHlavni = functions.vzdalenostMeziDvemaBody(meshKoty.vertices[0].co,meshKoty.vertices[28].co)
                self.odsazeniZakladna = functions.vzdalenostMeziDvemaBody(meshKoty.vertices[8].co,meshKoty.vertices[28].co)
                self.delkaSikmeCar = functions.vzdalenostMeziDvemaBody(meshKoty.vertices[4].co,meshKoty.vertices[20].co)
                self.delkaSikmeCar = self.delkaSikmeCar/0.7
                self.tloustka = functions.vzdalenostMeziDvemaBody(meshKoty.vertices[9].co,meshKoty.vertices[10].co)
                self.presahKolmice = functions.vzdalenostMeziDvemaBody(meshKoty.vertices[0].co,meshKoty.vertices[14].co)
                self.protazeni = functions.vzdalenostMeziDvemaBody(meshKoty.vertices[0].co,meshKoty.vertices[14].co)
                self.rotace = int(math.degrees(objectKoty.rotation_euler[0]))
                typeTmp = 'Arrow in out'
                testKonec = functions.indetifyText(self, context, objectTextu, objectKoty, meshKoty, typeTmp)
                if testKonec == False:
                    self.report({'ERROR'}, "Selected object is not valid dimension (unknown text in annotation)")
                    return {'CANCELLED'}

            elif intType == 2: #delame arrowout complet

                context.scene.DIMENSION.dimType = 'Arrow out'

                self.bod1 = objectKoty.matrix_world @ meshKoty.vertices[28].co
                self.bod2 = objectKoty.matrix_world @ meshKoty.vertices[29].co

                self.odsazeniHlavni = functions.vzdalenostMeziDvemaBody(meshKoty.vertices[0].co,meshKoty.vertices[28].co)
                self.odsazeniZakladna = functions.vzdalenostMeziDvemaBody(meshKoty.vertices[10].co,meshKoty.vertices[28].co)
                self.delkaSikmeCar = functions.vzdalenostMeziDvemaBody(meshKoty.vertices[3].co,meshKoty.vertices[22].co)
                self.delkaSikmeCar = self.delkaSikmeCar/0.7
                self.tloustka = functions.vzdalenostMeziDvemaBody(meshKoty.vertices[11].co,meshKoty.vertices[12].co)
                self.presahKolmice = functions.vzdalenostMeziDvemaBody(meshKoty.vertices[0].co,meshKoty.vertices[16].co)
                self.protazeni = functions.vzdalenostMeziDvemaBody(meshKoty.vertices[0].co,meshKoty.vertices[16].co)
                self.rotace = int(math.degrees(objectKoty.rotation_euler[0]))
                typeTmp = 'Arrow in out'
                testKonec = functions.indetifyText(self, context, objectTextu, objectKoty, meshKoty, typeTmp)
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

            self.odsazeniHlavni = functions.vzdalenostMeziDvemaBody(meshKoty.vertices[0].co,meshKoty.vertices[32].co)
            self.odsazeniZakladna = functions.vzdalenostMeziDvemaBody(meshKoty.vertices[8].co,meshKoty.vertices[32].co)
            self.delkaSikmeCar = functions.vzdalenostMeziDvemaBody(meshKoty.vertices[4].co,meshKoty.vertices[20].co)
            self.delkaSikmeCar =  self.delkaSikmeCar * 2
            self.tloustka = functions.vzdalenostMeziDvemaBody(meshKoty.vertices[9].co,meshKoty.vertices[10].co)
            self.presahKolmice = functions.vzdalenostMeziDvemaBody(meshKoty.vertices[0].co,meshKoty.vertices[14].co)
            self.protazeni = functions.vzdalenostMeziDvemaBody(meshKoty.vertices[0].co,meshKoty.vertices[14].co)
            self.rotace = int(math.degrees(objectKoty.rotation_euler[0]))
            typeTmp = 'Arrow open'
            testKonec = functions.indetifyText(self, context, objectTextu, objectKoty, meshKoty, typeTmp)
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

    
    