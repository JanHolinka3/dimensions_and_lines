import bpy #type: ignore
import bmesh #type: ignore
import math
import mathutils #type: ignore
from . import functions

def vytvorKotuSlope(self) -> bpy.types.Object:

    context = bpy.context

    zalohaCursoru = context.scene.cursor.location.copy()
    zalohaRotaceCusoru = context.scene.cursor.rotation_euler.copy()

    #vytvorime novy objekt
    for porad in range(3):
        context.scene.cursor.location[porad] = 0
        context.scene.cursor.rotation_euler[porad] = 0

    #prihodime text
    #bpy.ops.object.text_add()

    #test
    # Vytvoření nového textového objektu
    objectTextu = bpy.data.objects.new(name="text", object_data=bpy.data.curves.new(name="text", type='FONT'))
    # Přidání objektu do aktuální kolekce
    bpy.context.collection.objects.link(objectTextu)
    # Nastavení aktivního a vybraného objektu
    bpy.context.view_layer.objects.active = objectTextu
    objectTextu.select_set(True)

    #objectTextu = context.active_object
    self.ObjektTextu = objectTextu
    objectTextu.data.font = bpy.data.fonts[context.scene.DIMENSION.fontsArray]

    
    #bpy.ops.mesh.primitive_plane_add()
    #test
    # Vytvoření nového Mesh objektu
    objectMesh = bpy.data.meshes.new(name="dimension")
    objectKoty = bpy.data.objects.new(name="dimension", object_data=objectMesh)

    # Přidání do aktivní kolekce 
    bpy.context.collection.objects.link(objectKoty)

    # Vytvoření bmesh geometrie (rovina 2x2 Blender jednotky)
    #bm = bmesh.new()
    #bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=2.0)
    #bm.to_mesh(objectMesh)
    #bm.free()  # Uvolnění paměti

    # Nastavení aktivního a vybraného objektu - maybe not needed
    bpy.context.view_layer.objects.active = objectKoty
    objectKoty.select_set(True)



    #objectKoty = context.active_object
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

    #objectMesh = context.active_object.data
    #bpy.ops.object.mode_set(mode='EDIT')
    #bpy.ops.mesh.delete(type='EDGE_FACE') #pridana plane ma vsechno selected
    #bpy.ops.object.mode_set(mode='OBJECT')

    objectMesh.vertices.add(50)

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
    #bpy.ops.object.parent_set(type='OBJECT', xmirror=False, keep_transform=True)

    #test
    # Nastavení rodiče
    objectTextu.parent = objectKoty
    # Pokud chceš zachovat transformaci jako `keep_transform=True`
    objectTextu.matrix_parent_inverse = objectKoty.matrix_world.inverted()


    context.scene.cursor.location = zalohaCursoru
    context.scene.cursor.rotation_euler = zalohaRotaceCusoru

    return [objectKoty,objectTextu]

def osadKotuSlope(self, listKotaText, listVeci):
    context = bpy.context

    zalohaCursoru = context.scene.cursor.location.copy()
    
    for porad in range(3):
        context.scene.cursor.location[porad] = 0

    objectKoty = listKotaText[0]

    #self.ObjektKoty = objectKoty

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
    stredKoty = functions.vratBodMeziDvemaBody(kotaBaseVert1, kotaBaseVert2) #stred koty uvnitr objektu
    for porad in range(3):
        objectKoty.location[porad] = stredKoty[porad]
    
    #nastavime rotaci koty podle vektoru
    functions.rotaceDvaBody(objectKoty, kotaBaseVert1, kotaBaseVert2)

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
    kotaBaseVert1 = functions.pripoctiY(kotaBaseVert1, self.odsazeniHlavni) #Y je jakoby KOLMO
    objectMesh.vertices[pocetVert].co = kotaBaseVert1
    kotaBaseVert1Poradi = pocetVert

    #kotaBaseVert2 = self.odsad(kotaBaseVert2, vektorSmer, 2, self.odsazeniHlavni)
    kotaBaseVert2 = functions.pripoctiY(kotaBaseVert2, self.odsazeniHlavni)
    pocetVert += 1
    objectMesh.vertices[pocetVert].co = kotaBaseVert2
    kotaBaseVert2Poradi = pocetVert

    #resi svislost - protoze kota je v ZX plane a taha se vzdy kladne, tedy pokud je bod 2 nad bodem 1 (podle Z souradnice), tak musi byt pricitane hodnoty zaporne - jenom u pripoctiX
    selfProtazeniCopy = self.protazeni
    selfTloustkaCopy = self.tloustka
    selfDelkaSikmeCarCopy = self.delkaSikmeCar

    if listVeci[0][0] == listVeci[1][0] and listVeci[0][1] == listVeci[1][1]:
        if listVeci[0][2] > listVeci[1][2]:
            selfProtazeniCopy = -selfProtazeniCopy
            selfTloustkaCopy = -selfTloustkaCopy
            selfDelkaSikmeCarCopy = -selfDelkaSikmeCarCopy

    #body prodlouzeni
    pocetVert += 1
    kotaBaseVert1prodl = functions.pripoctiX(kotaBaseVert1, selfProtazeniCopy)
    objectMesh.vertices[pocetVert].co = kotaBaseVert1prodl

    pocetVert += 1 
    kotaBaseVert2prodl = functions.pripoctiX(kotaBaseVert2, -selfProtazeniCopy)
    objectMesh.vertices[pocetVert].co = kotaBaseVert2prodl

    #pridam body vlevo a vpravo dle poloviny tloustka 4 + 4 a 4 + 4
    #4 kolem hlavni vpravo
    pocetVert += 1 
    bodSirky1 = functions.pripoctiX(objectMesh.vertices[kotaBaseVert1Poradi].co, -selfTloustkaCopy/2)
    objectMesh.vertices[pocetVert].co = bodSirky1
    bodSirky1 = functions.pripoctiY(objectMesh.vertices[pocetVert].co, self.tloustka/2)
    objectMesh.vertices[pocetVert].co = bodSirky1
    pocetVert += 1
    bodSirky1 = functions.pripoctiX(objectMesh.vertices[kotaBaseVert1Poradi].co, selfTloustkaCopy/2)  
    objectMesh.vertices[pocetVert].co = bodSirky1
    bodSirky1 = functions.pripoctiY(objectMesh.vertices[pocetVert].co, self.tloustka/2)
    objectMesh.vertices[pocetVert].co = bodSirky1
    pocetVert += 1
    bodSirky1 = functions.pripoctiX(objectMesh.vertices[kotaBaseVert1Poradi].co, -selfTloustkaCopy/2)  
    objectMesh.vertices[pocetVert].co = bodSirky1
    bodSirky1 = functions.pripoctiY(objectMesh.vertices[pocetVert].co, -self.tloustka/2)
    objectMesh.vertices[pocetVert].co = bodSirky1
    pocetVert += 1
    bodSirky1 = functions.pripoctiX(objectMesh.vertices[kotaBaseVert1Poradi].co, selfTloustkaCopy/2)  
    objectMesh.vertices[pocetVert].co = bodSirky1
    bodSirky1 = functions.pripoctiY(objectMesh.vertices[pocetVert].co, -self.tloustka/2)
    objectMesh.vertices[pocetVert].co = bodSirky1
    #4 kolem hlavni vlevo
    pocetVert += 1
    bodSirky1 = functions.pripoctiX(objectMesh.vertices[kotaBaseVert2Poradi].co, -selfTloustkaCopy/2)  
    objectMesh.vertices[pocetVert].co = bodSirky1
    bodSirky1 = functions.pripoctiY(objectMesh.vertices[pocetVert].co, self.tloustka/2)
    objectMesh.vertices[pocetVert].co = bodSirky1
    pocetVert += 1
    bodSirky1 = functions.pripoctiX(objectMesh.vertices[kotaBaseVert2Poradi].co, selfTloustkaCopy/2)  
    objectMesh.vertices[pocetVert].co = bodSirky1
    bodSirky1 = functions.pripoctiY(objectMesh.vertices[pocetVert].co, self.tloustka/2)
    objectMesh.vertices[pocetVert].co = bodSirky1
    pocetVert += 1
    bodSirky1 = functions.pripoctiX(objectMesh.vertices[kotaBaseVert2Poradi].co, -selfTloustkaCopy/2)  
    objectMesh.vertices[pocetVert].co = bodSirky1
    bodSirky1 = functions.pripoctiY(objectMesh.vertices[pocetVert].co, -self.tloustka/2)
    objectMesh.vertices[pocetVert].co = bodSirky1
    pocetVert += 1
    bodSirky1 = functions.pripoctiX(objectMesh.vertices[kotaBaseVert2Poradi].co, selfTloustkaCopy/2)  
    objectMesh.vertices[pocetVert].co = bodSirky1
    bodSirky1 = functions.pripoctiY(objectMesh.vertices[pocetVert].co, -self.tloustka/2)
    objectMesh.vertices[pocetVert].co = bodSirky1
    #protazeni v hlavnim smeru vlevo a pak vpravo
    pocetVert += 1
    bodSirky1 = functions.pripoctiY(objectMesh.vertices[3].co, self.tloustka/2)
    objectMesh.vertices[pocetVert].co = bodSirky1
    pocetVert += 1
    bodSirky1 = functions.pripoctiY(objectMesh.vertices[3].co, -self.tloustka/2)
    objectMesh.vertices[pocetVert].co = bodSirky1
    pocetVert += 1
    bodSirky1 = functions.pripoctiY(objectMesh.vertices[2].co, self.tloustka/2)
    objectMesh.vertices[pocetVert].co = bodSirky1
    pocetVert += 1
    bodSirky1 = functions.pripoctiY(objectMesh.vertices[2].co, -self.tloustka/2)
    objectMesh.vertices[pocetVert].co = bodSirky1

    #spodni vpravo - stred,vlevo,vpravo
    pocetVert += 1
    kotaKolmiceSpodek1 = functions.pripoctiY(kotaBaseVert1Original, self.odsazeniZakladna)
    objectMesh.vertices[pocetVert].co = kotaKolmiceSpodek1
    pocetVert += 1
    bodSirky1 = functions.pripoctiX(objectMesh.vertices[pocetVert - 1].co, -selfTloustkaCopy/2)  
    objectMesh.vertices[pocetVert].co = bodSirky1
    pocetVert += 1
    bodSirky1 = functions.pripoctiX(objectMesh.vertices[pocetVert - 2].co, selfTloustkaCopy/2)  
    objectMesh.vertices[pocetVert].co = bodSirky1
    #spodni vlevo - stred,vlevo,vpravo
    pocetVert += 1
    kotaKolmiceSpodek2 = functions.pripoctiY(kotaBaseVert2Original, self.odsazeniZakladna)
    objectMesh.vertices[pocetVert].co = kotaKolmiceSpodek2
    pocetVert += 1
    bodSirky1 = functions.pripoctiX(objectMesh.vertices[pocetVert - 1].co, -selfTloustkaCopy/2)  
    objectMesh.vertices[pocetVert].co = bodSirky1
    pocetVert += 1
    bodSirky1 = functions.pripoctiX(objectMesh.vertices[pocetVert - 2].co, selfTloustkaCopy/2)  
    objectMesh.vertices[pocetVert].co = bodSirky1
    #horni vpravo - stred,vlevo,vpravo
    pocetVert += 1
    kotaKolmiceVrsek1 = functions.pripoctiY(kotaBaseVert1, self.presahKolmice)
    objectMesh.vertices[pocetVert].co = kotaKolmiceVrsek1
    pocetVert += 1
    bodSirky1 = functions.pripoctiX(objectMesh.vertices[pocetVert - 1].co, -selfTloustkaCopy/2)  
    objectMesh.vertices[pocetVert].co = bodSirky1
    pocetVert += 1
    bodSirky1 = functions.pripoctiX(objectMesh.vertices[pocetVert - 2].co, selfTloustkaCopy/2)  
    objectMesh.vertices[pocetVert].co = bodSirky1
    #horni vlevo - stred,vlevo,vpravo
    pocetVert += 1
    kotaKolmiceVrsek2 = functions.pripoctiY(kotaBaseVert2, self.presahKolmice)
    objectMesh.vertices[pocetVert].co = kotaKolmiceVrsek2
    pocetVert += 1
    bodSirky1 = functions.pripoctiX(objectMesh.vertices[pocetVert - 1].co, -selfTloustkaCopy/2)  
    objectMesh.vertices[pocetVert].co = bodSirky1
    pocetVert += 1
    bodSirky1 = functions.pripoctiX(objectMesh.vertices[pocetVert - 2].co, selfTloustkaCopy/2)  
    objectMesh.vertices[pocetVert].co = bodSirky1

    #sikmina vpravo horni stred
    pocetVert +=1
    bodSirky1=functions.pripoctiY(objectMesh.vertices[0].co,math.sin(45/(180/math.pi))*(self.delkaSikmeCar/2))
    objectMesh.vertices[pocetVert].co = bodSirky1
    bodSirky1=functions.pripoctiX(objectMesh.vertices[pocetVert].co,math.sin(45/(180/math.pi))*(selfDelkaSikmeCarCopy/2))
    objectMesh.vertices[pocetVert].co = bodSirky1
    #sikmina vpravo spodni stred
    pocetVert +=1
    bodSirky1=functions.pripoctiY(objectMesh.vertices[0].co,-math.sin(45/(180/math.pi))*(self.delkaSikmeCar/2))
    objectMesh.vertices[pocetVert].co = bodSirky1
    bodSirky1=functions.pripoctiX(objectMesh.vertices[pocetVert].co,-math.sin(45/(180/math.pi))*(selfDelkaSikmeCarCopy/2))
    objectMesh.vertices[pocetVert].co = bodSirky1

    #sikmina vpravo horni stred odsazeni
    pocetVert +=1
    bodSirky1=functions.pripoctiY(objectMesh.vertices[pocetVert-2].co,(-self.tloustka/2)*math.sin(45/(180/math.pi)))
    bodSirky1=functions.pripoctiX(bodSirky1,math.sin(45/(180/math.pi))*(selfTloustkaCopy/2))
    objectMesh.vertices[pocetVert].co = bodSirky1
    pocetVert +=1
    bodSirky1=functions.pripoctiY(objectMesh.vertices[pocetVert-3].co,(self.tloustka/2)*math.sin(45/(180/math.pi)))
    bodSirky1=functions.pripoctiX(bodSirky1,math.sin(45/(180/math.pi))*(-selfTloustkaCopy/2))
    objectMesh.vertices[pocetVert].co = bodSirky1

    #sikmina vpravo spodni stred odsazeni
    pocetVert +=1
    bodSirky1=functions.pripoctiY(objectMesh.vertices[pocetVert-3].co,(-self.tloustka/2)*math.sin(45/(180/math.pi)))
    bodSirky1=functions.pripoctiX(bodSirky1,math.sin(45/(180/math.pi))*(selfTloustkaCopy/2))
    objectMesh.vertices[pocetVert].co = bodSirky1
    pocetVert +=1
    bodSirky1=functions.pripoctiY(objectMesh.vertices[pocetVert-4].co,(self.tloustka/2)*math.sin(45/(180/math.pi)))
    bodSirky1=functions.pripoctiX(bodSirky1,math.sin(45/(180/math.pi))*(-selfTloustkaCopy/2))
    objectMesh.vertices[pocetVert].co = bodSirky1

    #horni diagonala pro diagonalu - obe
    pocetVert +=1
    bodSirky1=functions.pripoctiX(objectMesh.vertices[5].co,(selfTloustkaCopy/2)/math.sin(45/(180/math.pi)))
    objectMesh.vertices[pocetVert].co = bodSirky1
    pocetVert +=1   
    bodSirky1=functions.pripoctiY(objectMesh.vertices[5].co,(self.tloustka/2)/math.sin(45/(180/math.pi)))
    objectMesh.vertices[pocetVert].co = bodSirky1

    #spodni diagonala pro diagonalu - obe
    pocetVert +=1
    bodSirky1=functions.pripoctiX(objectMesh.vertices[6].co,(-selfTloustkaCopy/2)/math.sin(45/(180/math.pi)))
    objectMesh.vertices[pocetVert].co = bodSirky1
    pocetVert +=1   
    bodSirky1=functions.pripoctiY(objectMesh.vertices[6].co,(-self.tloustka/2)/math.sin(45/(180/math.pi)))
    objectMesh.vertices[pocetVert].co = bodSirky1

    #sikmina vlevo horni stred
    pocetVert +=1
    bodSirky1=functions.pripoctiY(objectMesh.vertices[1].co,math.sin(45/(180/math.pi))*(self.delkaSikmeCar/2))
    objectMesh.vertices[pocetVert].co = bodSirky1
    bodSirky1=functions.pripoctiX(objectMesh.vertices[pocetVert].co,math.sin(45/(180/math.pi))*(selfDelkaSikmeCarCopy/2))
    objectMesh.vertices[pocetVert].co = bodSirky1
    #sikmina vlevo spodni stred
    pocetVert +=1
    bodSirky1=functions.pripoctiY(objectMesh.vertices[1].co,-math.sin(45/(180/math.pi))*(self.delkaSikmeCar/2))
    objectMesh.vertices[pocetVert].co = bodSirky1
    bodSirky1=functions.pripoctiX(objectMesh.vertices[pocetVert].co,-math.sin(45/(180/math.pi))*(selfDelkaSikmeCarCopy/2))
    objectMesh.vertices[pocetVert].co = bodSirky1

    #sikmina vlevo horni stred odsazeni
    pocetVert +=1
    bodSirky1=functions.pripoctiY(objectMesh.vertices[pocetVert-2].co,(-self.tloustka/2)*math.sin(45/(180/math.pi)))
    bodSirky1=functions.pripoctiX(bodSirky1,math.sin(45/(180/math.pi))*(selfTloustkaCopy/2))
    objectMesh.vertices[pocetVert].co = bodSirky1
    pocetVert +=1
    bodSirky1=functions.pripoctiY(objectMesh.vertices[pocetVert-3].co,(self.tloustka/2)*math.sin(45/(180/math.pi)))
    bodSirky1=functions.pripoctiX(bodSirky1,math.sin(45/(180/math.pi))*(-selfTloustkaCopy/2))
    objectMesh.vertices[pocetVert].co = bodSirky1

    #sikmina vlevo spodni stred odsazeni
    pocetVert +=1
    bodSirky1=functions.pripoctiY(objectMesh.vertices[pocetVert-3].co,(-self.tloustka/2)*math.sin(45/(180/math.pi)))
    bodSirky1=functions.pripoctiX(bodSirky1,math.sin(45/(180/math.pi))*(selfTloustkaCopy/2))
    objectMesh.vertices[pocetVert].co = bodSirky1
    pocetVert +=1
    bodSirky1=functions.pripoctiY(objectMesh.vertices[pocetVert-4].co,(self.tloustka/2)*math.sin(45/(180/math.pi)))
    bodSirky1=functions.pripoctiX(bodSirky1,math.sin(45/(180/math.pi))*(-selfTloustkaCopy/2))
    objectMesh.vertices[pocetVert].co = bodSirky1

    #horni diagonala pro diagonalu - obe
    pocetVert +=1
    bodSirky1=functions.pripoctiX(objectMesh.vertices[9].co,(selfTloustkaCopy/2)/math.sin(45/(180/math.pi)))
    objectMesh.vertices[pocetVert].co = bodSirky1
    pocetVert +=1   
    bodSirky1=functions.pripoctiY(objectMesh.vertices[9].co,(self.tloustka/2)/math.sin(45/(180/math.pi)))
    objectMesh.vertices[pocetVert].co = bodSirky1

    #spodni diagonala pro diagonalu - obe
    pocetVert +=1
    bodSirky1=functions.pripoctiX(objectMesh.vertices[10].co,(-selfTloustkaCopy/2)/math.sin(45/(180/math.pi)))
    objectMesh.vertices[pocetVert].co = bodSirky1
    pocetVert +=1   
    bodSirky1=functions.pripoctiY(objectMesh.vertices[10].co,(-self.tloustka/2)/math.sin(45/(180/math.pi)))
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
    stredKotyOdsaz = functions.vratBodMeziDvemaBody(kotaBaseVert1, kotaBaseVert2)
    for porad in range(3):
        objectTextu.location[porad] = stredKotyOdsaz[porad]
        
    #nastavime rotaci koty podle vektoru
    functions.rotaceDvaBody(objectTextu, kotaBaseVert1, kotaBaseVert2)

    KotaNumber = functions.vzdalenostMeziDvemaBody(kotaBaseVert1,kotaBaseVert2)
    KotaNumber = KotaNumber * self.distanceScale
    #tady uz bych to mohl oddelit podle ft in a metric
    if context.scene.DIMENSION.jednotky == 'ft in':
        textKoty = functions.makeImperial(self, context, KotaNumber)
    elif context.scene.DIMENSION.jednotky == 'inches':
        textKoty = functions.makeInches(self, context, KotaNumber)
    else:
        textKoty = str(round(KotaNumber, self.pocetDesetMist))
        textKoty = functions.zaokrouhlNa(textKoty, self.pocetDesetMist)
        textKoty = functions.vymenTeckuZaCarku(textKoty)
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