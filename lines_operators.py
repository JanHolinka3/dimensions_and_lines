import bpy # type: ignore
import bmesh # type: ignore
import math

class MESH_OT_lines_clear(bpy.types.Operator):
    """Clear thickness"""
    bl_idname = "mesh.lines_clear"
    bl_label = "Clear Lines"

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'
    
    def execute(self, context):

        #pridat kontrolu odpovidajiciho objektu
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
        
        meshObjektuCar = bpy.context.active_object.data
        boolContainOnlyVisible = True  
        for vert in meshObjektuCar.vertices:
            if vert.hide == True:
                boolContainOnlyVisible = False
                break
        if boolContainOnlyVisible == True:
            self.report({'ERROR'}, "Selected object have only visible vertices. There is nothing to clear.")
            return {'CANCELLED'}

        objectMesh = bpy.context.active_object.data

        bFA=bmesh.new()   
        bFA.from_mesh(objectMesh)
        bFA.verts.ensure_lookup_table()

        vertListDel = []
        for vert in bFA.verts:
            if vert.hide == True:
                vertListDel.append(vert)
        bmesh.ops.delete(bFA, geom=vertListDel, context='VERTS') #vymazu hidden, radeji s bmesh

        bFA.to_mesh(objectMesh)
        bFA.free() 

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.mode_set(mode='OBJECT')

        return{'FINISHED'}

class MESH_OT_lines(bpy.types.Operator):
    """Add thicknes to edges (also erase existing hatches)"""
    bl_idname = "mesh.lines"
    bl_label = "Lines"
    bl_options = {'REGISTER', 'UNDO'}

    tloustka: bpy.props.FloatProperty(name="thickness",description="line thickness",default=0.1,min = 0,step=1, precision= 3) # type: ignore
    dashSpace: bpy.props.FloatProperty(name="space length", description="space between dashes", default=0.3, min = 0,step=1, precision= 3) # type: ignore
    dashLine: bpy.props.FloatProperty(name="line length", description="dash line length", default=1.2, min = 0,step=1, precision= 3) # type: ignore
    dotSize: bpy.props.FloatProperty(name="dot size", description="do size length", default=0.1, min = 0,step=1, precision= 3) # type: ignore
    boolFirstRun: bpy.props.BoolProperty(name="firstRun", description="determine if it is called from UI", default=False, options={'HIDDEN'}) # type: ignore
    #typ: bpy.props.IntProperty(name="type",description="type of line",default=0,min = 0,max = 3,)

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'
    
    def execute(self, context):
        
        #pridat kontrolu odpovidajiciho objektu
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
        
        meshObjektuCar = bpy.context.active_object.data
        for face in meshObjektuCar.polygons:
            if face.hide == False:
                self.report({'ERROR'}, "Selected object have visible faces. Add thickness is meant only for objects with no, or invisible faces.")
                return {'CANCELLED'}
        boolContainEdges = False
        boolDiferenceZlocation = False
        Zloc = 0.0
        firstLocation = False
        kontrolaFin = False
        for edge in meshObjektuCar.edges:
            if firstLocation == False:
                Zloc = meshObjektuCar.vertices[edge.vertices[0]].co[2]
            firstLocation = True
            if kontrolaFin == False:
                if math.isclose(meshObjektuCar.vertices[edge.vertices[0]].co[2], Zloc,abs_tol=0.00001) == False:
                    kontrolaFin = True
                    self.report({'WARNING'}, "Edges in selected object are not flatten out/aligned to X-Y plane. Created lines are flattened/aligned to X-Y plane. To achieve different angle, please rotate the whole object.")
                if math.isclose(meshObjektuCar.vertices[edge.vertices[1]].co[2], Zloc,abs_tol=0.00001) == False:
                    kontrolaFin = True
                    self.report({'WARNING'}, "Edges in selected object are not flatten out/aligned to X-Y plane. Created lines are flattened/aligned to X-Y plane. To achieve different angle, please rotate the whole object.")
            if edge.hide == False:
                boolContainEdges = True

        if boolContainEdges == False:
            self.report({'ERROR'}, "Selected object have no visible edges. Add thickness is adding geometry only on visible edges.")
            return {'CANCELLED'}

        if context.scene.DIMENSION.ignoreUndo == True:
            if self.boolFirstRun == True:
                if context.scene.DIMENSION.lineWidths == 'Normal':
                    self.tloustka = 0.00028*context.scene.DIMENSION.scale
                if context.scene.DIMENSION.lineWidths == 'Thin':
                    self.tloustka = 0.00014*context.scene.DIMENSION.scale  
                if context.scene.DIMENSION.lineWidths == 'Thick':
                    self.tloustka = 0.0006*context.scene.DIMENSION.scale
                if context.scene.DIMENSION.lineWidths == 'Very Thick':
                    self.tloustka = 0.0012*context.scene.DIMENSION.scale

                self.dashSpace = 3.5 * self.tloustka
                self.dashLine = 12 * self.tloustka
                self.dotSize = 1 * self.tloustka
                self.boolFirstRun = False

        if bpy.context.active_object.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        self.dotSize = 1 * self.tloustka

        ObjektCar = bpy.context.active_object

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

        if ObjektCar.data.materials.items() == []:
            ObjektCar.data.materials.append(material)

        bFA=bmesh.new()   
        bFA.from_mesh(meshObjektuCar)
        bFA.verts.ensure_lookup_table()

        vertListDel = []
        for vert in bFA.verts:
            if vert.hide == True:
                vertListDel.append(vert)
        bmesh.ops.delete(bFA, geom=vertListDel, context='VERTS') #vymazu hidden, radeji s bmesh

        #zatim pro kazdy edge vytvorim funkci odsad na jednu a na druhou stranu dve vertices a ty spojim s temi vychozimi dvema vertices ve face - to by jako pri nejhorsim mohlo projit
        vertListKoncove = []
        for vert in bFA.verts:
            if len(vert.link_edges) == 1:
                vertListKoncove.append(vert) #tohle mozna nakonec vyhodime

        vertListKompletBase = []
        vertListKompletBase.clear()
        for vert in bFA.verts:
            vertListKompletBase.append(vert)

        edgesList = []
        
        for edges in bFA.edges:
            edgesList.append(edges)

        listForBevel=[]

        if context.scene.DIMENSION.lineTypes == 'Straight': #PONECHAT JAKO SIMPLETON VERZI!!!! uzaviret vsechny edges ze vsech stran - neni idealni, ale vzhledem k ucelu pouziti naprosto dostatecne pro bezne ucely
            for edges in edgesList: #pro kazdy edge
                vertice1=edges.verts[0].co  #vytahnu jeho dve vert
                vertice2=edges.verts[1].co  
                smeroyVektor=self.smerovyVektor(vertice1,vertice2) #vypocitam z nich smerovy vektor kvuli odsazovani na kolmici a primo
                #jedna strana
                vertice3 = bFA.verts.new(self.odsad(vertice1,smeroyVektor,2,self.tloustka/2)) 
                listForBevel.append(vertice3)
                vertice4 = bFA.verts.new(self.odsad(vertice2,smeroyVektor,2,self.tloustka/2))
                listForBevel.append(vertice4)

                vertice3.co = self.pripoctiNejOsa(vertice3.co,smeroyVektor,-self.tloustka/2)
                vertice4.co = self.pripoctiNejOsa(vertice4.co,smeroyVektor,self.tloustka/2)

                #druha strana
                vertice5 = bFA.verts.new(self.odsad(vertice1,smeroyVektor,2,-self.tloustka/2))
                listForBevel.append(vertice5)
                vertice6 = bFA.verts.new(self.odsad(vertice2,smeroyVektor,2,-self.tloustka/2))
                listForBevel.append(vertice6)

                vertice5.co = self.pripoctiNejOsa(vertice5.co,smeroyVektor,-self.tloustka/2)
                vertice6.co = self.pripoctiNejOsa(vertice6.co,smeroyVektor,self.tloustka/2)

                bFA.faces.new([vertice4,vertice3,vertice5,vertice6])    

                vertice3.hide_set(True)
                vertice4.hide_set(True)
                vertice5.hide_set(True)
                vertice6.hide_set(True) 

        if context.scene.DIMENSION.lineTypes == '...':#testujeme jine metody
            for vert in bFA.verts:
                print()
                if len(vert.link_edges) == 2:
                    angle = vert.calc_edge_angle()
                    vert.calc_shell_factor
                    vert.normal
                    print(angle)

        #odsazovani se bude muset nejak resit podle uhlu - self.tloustka/2 je maximalni odsazeni - ktere se bude nejak dopocitavat podle uhlu, pokud vyjde vetsi, 
                #vytvori se 2 body a trouhlenik mezi nimi , pokud mensi, tak bod je jenom jeden - tam bude problem s identifikaci a napojovanim bodu mezi sebou - spis se asi nechaji oba body a pak se to projede mergem... body se budou posouvat pod 90 stupnu podle 
                
                #novy napad: pro kazdou vert se vezme prvni nalezeny with connected edges jedna od toho se pokracuje na dalsi vert, pokud rovno 1 tak se vracime, pri dojeti na vychozi vert se konci, a nebo se sleduje stopa, pro kazdou vert se potom udela list edges a poradi podle velikosti sviraneho uhlu,
                # to se postupne likviduje pri dalsich navstevach vert, musi se akorat hlidat smer - asi po smeru hodinovych rucicek. to se nejdriv otestuje na simple line
                
                #nejakej trigonometrie

            #vezmu smerovyVektor - odsadim uplne stejne jako typ0 ale jenom na verts[0], od toho zase odsazuju podle delky cary, pak mesh - 
            #kontrola preteceni s podminkou pro zkraceni a continue (vcetne hide_set), pak odsazeni podle delky mezery - kontrola preteceni s podminkou pro vymaz a continue (vcetne hide_set)
            for edges in edgesList:
                pass

            #odsazovani se bude muset nejak resit podle uhlu - self.tloustka/2 je maximalni odsazeni - ktere se bude nejak dopocitavat podle uhlu, pokud vyjde vetsi, 
                #vytvori se 2 body a trouhlenik mezi nimi , pokud mensi, tak bod je jenom jeden - tam bude problem s identifikaci a napojovanim bodu mezi sebou - spis se asi nechaji oba body a pak se to projede mergem... body se budou posouvat pod 90 stupnu podle 
                
                #novy napad: pro kazdou vert se vezme prvni nalezeny with connected edges jedna od toho se pokracuje na dalsi vert, pokud rovno 1 tak se vracime, pri dojeti na vychozi vert se konci, a nebo se sleduje stopa, pro kazdou vert se potom udela list edges a poradi podle velikosti sviraneho uhlu,
                # to se postupne likviduje pri dalsich navstevach vert, musi se akorat hlidat smer - asi po smeru hodinovych rucicek. to se nejdriv otestuje na simple line
            
                #nejakej trigonometrie

        if context.scene.DIMENSION.lineTypes == 'Dashed': #teckovana cara - to je vlastne carkovana, akorat delka cary mensi a je zaroven tloustkou            
            for edges in edgesList: #pro kazdy edge
                vertice1 = edges.verts[0]  #vytahnu jeho dve vert
                vertice2 = edges.verts[1] 
                smeroyVektor=self.smerovyVektor(vertice1.co,vertice2.co) #vypocitam z nich smerovy vektor kvuli odsazovani na kolmici a primo
                #jedna strana
                vzdalenost = self.vzdalenostMeziDvemaBody(vertice1.co, vertice2.co)
                paintedDist = 0

                firstRun = True
                #pridavat budu dokud nevycerpam vzdalenost 
                while paintedDist < vzdalenost:
                    #prvni dve tecky
                    if paintedDist + self.dashSpace > vzdalenost:
                        if firstRun == False:
                            break 

                    if firstRun == True:
                        vertice3 = bFA.verts.new(self.odsad(vertice1.co,smeroyVektor,2,self.tloustka/2)) 
                        listForBevel.append(vertice3)
                        vertice4 = bFA.verts.new(self.odsad(vertice1.co,smeroyVektor,2,-self.tloustka/2))
                        listForBevel.append(vertice4)
                        vertice3.co = self.pripoctiNejOsa(vertice3.co,smeroyVektor,-self.tloustka/2)
                        vertice4.co = self.pripoctiNejOsa(vertice4.co,smeroyVektor,-self.tloustka/2)
                        firstRun = False
                    else:
                        vertice3 = bFA.verts.new(vertice5.co)
                        listForBevel.append(vertice3)
                        vertice4 = bFA.verts.new(vertice6.co)
                        listForBevel.append(vertice4)
                        vertice3.co = self.pripoctiNejOsa(vertice3.co,smeroyVektor,self.dashSpace)
                        vertice4.co = self.pripoctiNejOsa(vertice4.co,smeroyVektor,self.dashSpace)
                        paintedDist = paintedDist + self.dashSpace


                    vertice5 = bFA.verts.new(vertice3.co) 
                    listForBevel.append(vertice5)      
                    vertice6 = bFA.verts.new(vertice4.co)
                    listForBevel.append(vertice6)  

                    if paintedDist + self.dashLine > vzdalenost:
                        vertice5.co = self.pripoctiNejOsa(vertice5.co,smeroyVektor,vzdalenost - paintedDist + self.tloustka/2)
                        vertice6.co = self.pripoctiNejOsa(vertice6.co,smeroyVektor,vzdalenost - paintedDist + self.tloustka/2)
                    else:
                        vertice5.co = self.pripoctiNejOsa(vertice5.co,smeroyVektor,self.dashLine)
                        vertice6.co = self.pripoctiNejOsa(vertice6.co,smeroyVektor,self.dashLine)

                    paintedDist = paintedDist + self.dashLine

                    bFA.faces.new([vertice3, vertice4, vertice6, vertice5])

                    vertice3.hide_set(True)
                    vertice4.hide_set(True)
                    vertice5.hide_set(True)
                    vertice6.hide_set(True) 

        if context.scene.DIMENSION.lineTypes == 'Dotted': #teckovana cara - to je vlastne carkovana, akorat delka cary mensi a je zaroven tloustkou            
            for edges in edgesList: #pro kazdy edge
                vertice1 = edges.verts[0]  #vytahnu jeho dve vert
                vertice2 = edges.verts[1] 
                smeroyVektor=self.smerovyVektor(vertice1.co,vertice2.co) #vypocitam z nich smerovy vektor kvuli odsazovani na kolmici a primo
                #jedna strana
                vzdalenost = self.vzdalenostMeziDvemaBody(vertice1.co, vertice2.co)
                paintedDist = 0

                firstRun = True
                #pridavat budu dokud nevycerpam vzdalenost 
                while paintedDist < vzdalenost:
                    #prvni dve tecky
                    if paintedDist + self.dashSpace > vzdalenost: break 

                    if firstRun == True:
                        vertice3 = bFA.verts.new(self.odsad(vertice1.co,smeroyVektor,2,self.tloustka/2)) 
                        listForBevel.append(vertice3)
                        vertice4 = bFA.verts.new(self.odsad(vertice1.co,smeroyVektor,2,-self.tloustka/2))
                        listForBevel.append(vertice4)
                        vertice3.co = self.pripoctiNejOsa(vertice3.co,smeroyVektor,-self.tloustka/2)
                        vertice4.co = self.pripoctiNejOsa(vertice4.co,smeroyVektor,-self.tloustka/2)
                        firstRun = False
                    else:
                        vertice3 = bFA.verts.new(vertice5.co)
                        listForBevel.append(vertice3)
                        vertice4 = bFA.verts.new(vertice6.co)
                        listForBevel.append(vertice4)
                        vertice3.co = self.pripoctiNejOsa(vertice3.co,smeroyVektor,self.dashSpace)
                        vertice4.co = self.pripoctiNejOsa(vertice4.co,smeroyVektor,self.dashSpace)
                        paintedDist = paintedDist + self.dashSpace


                    vertice5 = bFA.verts.new(vertice3.co)  
                    listForBevel.append(vertice5)     
                    vertice6 = bFA.verts.new(vertice4.co)
                    listForBevel.append(vertice6)  

                    if paintedDist + self.dotSize > vzdalenost:
                        vertice5.co = self.pripoctiNejOsa(vertice5.co,smeroyVektor,vzdalenost - paintedDist + self.tloustka/2)
                        vertice6.co = self.pripoctiNejOsa(vertice6.co,smeroyVektor,vzdalenost - paintedDist + self.tloustka/2)
                    else:
                        vertice5.co = self.pripoctiNejOsa(vertice5.co,smeroyVektor,self.dotSize)
                        vertice6.co = self.pripoctiNejOsa(vertice6.co,smeroyVektor,self.dotSize)

                    paintedDist = paintedDist + self.dotSize

                    bFA.faces.new([vertice3, vertice4, vertice6, vertice5])

                    vertice3.hide_set(True)
                    vertice4.hide_set(True)
                    vertice5.hide_set(True)
                    vertice6.hide_set(True) 

                #odsazovani se bude muset nejak resit podle uhlu - self.tloustka/2 je maximalni odsazeni - ktere se bude nejak dopocitavat podle uhlu, pokud vyjde vetsi, 
                #vytvori se 2 body a trouhlenik mezi nimi , pokud mensi, tak bod je jenom jeden - tam bude problem s identifikaci a napojovanim bodu mezi sebou - spis se asi nechaji oba body a pak se to projede mergem... body se budou posouvat pod 90 stupnu podle 
                
                #novy napad: pro kazdou vert se vezme prvni nalezeny with connected edges jedna od toho se pokracuje na dalsi vert, pokud rovno 1 tak se vracime, pri dojeti na vychozi vert se konci, a nebo se sleduje stopa, pro kazdou vert se potom udela list edges a poradi podle velikosti sviraneho uhlu,
                # to se postupne likviduje pri dalsich navstevach vert, musi se akorat hlidat smer - asi po smeru hodinovych rucicek. to se nejdriv otestuje na simple line
                
                #nejakej trigonometrie

        switchCarka = False
        if context.scene.DIMENSION.lineTypes == 'Dash-dotted': #teckovana cara - to je vlastne carkovana, akorat delka cary mensi a je zaroven tloustkou            
            for edges in edgesList: #pro kazdy edge

                vertice1 = edges.verts[0]  #vytahnu jeho dve vert
                vertice2 = edges.verts[1] 
                smeroyVektor=self.smerovyVektor(vertice1.co,vertice2.co) #vypocitam z nich smerovy vektor kvuli odsazovani na kolmici a primo
                #jedna strana
                vzdalenost = self.vzdalenostMeziDvemaBody(vertice1.co, vertice2.co)
                paintedDist = 0

                firstRun = True
                #pridavat budu dokud nevycerpam vzdalenost 
                while paintedDist < vzdalenost:
                    #prvni dve tecky
                    if switchCarka == False:
                        switchCarka = True
                    else:
                        switchCarka = False

                    if paintedDist + self.dashSpace > vzdalenost: break 

                    if firstRun == True:
                        vertice3 = bFA.verts.new(self.odsad(vertice1.co,smeroyVektor,2,self.tloustka/2)) 
                        listForBevel.append(vertice3)
                        vertice4 = bFA.verts.new(self.odsad(vertice1.co,smeroyVektor,2,-self.tloustka/2))
                        listForBevel.append(vertice4)
                        vertice3.co = self.pripoctiNejOsa(vertice3.co,smeroyVektor,-self.tloustka/2)
                        vertice4.co = self.pripoctiNejOsa(vertice4.co,smeroyVektor,-self.tloustka/2)
                        firstRun = False
                    else:
                        vertice3 = bFA.verts.new(vertice5.co)
                        listForBevel.append(vertice3)
                        vertice4 = bFA.verts.new(vertice6.co)
                        listForBevel.append(vertice4)
                        vertice3.co = self.pripoctiNejOsa(vertice3.co,smeroyVektor,self.dashSpace)
                        vertice4.co = self.pripoctiNejOsa(vertice4.co,smeroyVektor,self.dashSpace)
                        paintedDist = paintedDist + self.dashSpace

                    vertice5 = bFA.verts.new(vertice3.co)  
                    listForBevel.append(vertice5)     
                    vertice6 = bFA.verts.new(vertice4.co)
                    listForBevel.append(vertice6)  

                    if switchCarka == True:
                        if paintedDist + self.dashLine > vzdalenost:
                            vertice5.co = self.pripoctiNejOsa(vertice5.co,smeroyVektor,vzdalenost - paintedDist + self.tloustka/2)
                            vertice6.co = self.pripoctiNejOsa(vertice6.co,smeroyVektor,vzdalenost - paintedDist + self.tloustka/2)
                        else:
                            vertice5.co = self.pripoctiNejOsa(vertice5.co,smeroyVektor,self.dashLine)
                            vertice6.co = self.pripoctiNejOsa(vertice6.co,smeroyVektor,self.dashLine)

                        paintedDist = paintedDist + self.dashLine

                    if switchCarka == False:
                        if paintedDist + self.dotSize > vzdalenost:
                            vertice5.co = self.pripoctiNejOsa(vertice5.co,smeroyVektor,vzdalenost - paintedDist + self.tloustka/2)
                            vertice6.co = self.pripoctiNejOsa(vertice6.co,smeroyVektor,vzdalenost - paintedDist + self.tloustka/2)
                        else:
                            vertice5.co = self.pripoctiNejOsa(vertice5.co,smeroyVektor,self.dotSize)
                            vertice6.co = self.pripoctiNejOsa(vertice6.co,smeroyVektor,self.dotSize)

                        paintedDist = paintedDist + self.dotSize

                    bFA.faces.new([vertice3, vertice4, vertice6, vertice5])

                    vertice3.hide_set(True)
                    vertice4.hide_set(True)
                    vertice5.hide_set(True)
                    vertice6.hide_set(True) 
                
        bmesh.ops.bevel(bFA, geom = listForBevel, offset=self.tloustka/3.5, affect='VERTICES',)
        #vertListKompletBase
        bFA.to_mesh(meshObjektuCar)
        bFA.free() 

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.mode_set(mode='OBJECT')
        return {'FINISHED'}
    
    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(self, "tloustka")
        if context.scene.DIMENSION.lineTypes == 'Dashed':
            row = layout.row()
            row.prop(self, "dashLine")
            row = layout.row()
            row.prop(self, "dashSpace")
        if context.scene.DIMENSION.lineTypes == 'Dotted':
            row = layout.row()
            row.prop(self, "dashSpace")
        if context.scene.DIMENSION.lineTypes == 'Dash-dotted':
            row = layout.row()
            row.prop(self, "dashLine")
            row = layout.row()
            row.prop(self, "dashSpace")

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