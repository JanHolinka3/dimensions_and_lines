import math
import mathutils # type: ignore
from timeit import default_timer as timer
import bpy # type: ignore

#return points of intersections of all edges in edgesList with edgeCut - edgelist is list of edges from bmesh and edge Cut is just list float x1 and y1 and x2 and y2
def vratStycneBody(edgesList, edgeCut, Zloc):   
    listbodu = []
    for edge in edgesList:
        boolJeToMimo = False
        max_X = edge.verts[0].co[0]
        if edge.verts[1].co[0] > max_X:
            max_X = edge.verts[1].co[0]
            
        min_X = edge.verts[0].co[0]
        if edge.verts[1].co[0] < min_X:
            min_X = edge.verts[1].co[0]

        max_Y = edge.verts[0].co[1]
        if edge.verts[1].co[1] > max_Y:
            max_Y = edge.verts[1].co[1]

        min_Y = edge.verts[0].co[1]
        if edge.verts[1].co[1] < min_Y:
            min_Y = edge.verts[1].co[1]
        
        bod1 = mathutils.Vector((edge.verts[0].co[0], edge.verts[0].co[1], Zloc))
        bod2 = mathutils.Vector((edge.verts[1].co[0], edge.verts[1].co[1], Zloc))
        bod3 = mathutils.Vector((edgeCut[0], edgeCut[1], Zloc))
        bod4 = mathutils.Vector((edgeCut[2], edgeCut[3], Zloc))

        bodiky = mathutils.geometry.intersect_line_line(bod1, bod2, bod3, bod4)

        if bodiky is not None:
            if bodiky[0][0] > max_X:
                boolJeToMimo = True
            if bodiky[0][0] < min_X:
                boolJeToMimo = True
            if bodiky[0][1] > max_Y:
                boolJeToMimo = True
            if bodiky[0][1] < min_Y:
                boolJeToMimo = True
        else:
            boolJeToMimo = True

        if boolJeToMimo == False:
            listbodu.append(bodiky[0])
        
    #sort bodiku, zkusime podle vzdalenosti od x1 a y1
    listVzdalenosti = []
    for bod in listbodu:
        #budem pro kazdy bod pocitat delku usecky z bodu edgeCut prvniho do daneho bodu - tyto vzdalenosti dame do float listu, pak tento sortnem a spolu s nim i listbodu
        vzdalenostBodu = vzdalenostMeziDvema2DBody((edgeCut[0], edgeCut[1]),(bod[0], bod[1]))
        listVzdalenosti.append(vzdalenostBodu)    

    #sort looping thru - start loop create clean true bool, swap make false, while swap false repeat
    swap = False
    while swap == False:
        swap = True
        for i in range(len(listVzdalenosti)):
            if i + 1 == len(listVzdalenosti):
                break
            if listVzdalenosti[i] > listVzdalenosti[i + 1]:
                tmp = listVzdalenosti[i]
                listVzdalenosti[i] = listVzdalenosti[i + 1]
                listVzdalenosti[i + 1] = tmp
                swap = False

                tmpBod = listbodu[i]
                listbodu[i] = listbodu[i + 1]
                listbodu[i + 1] = tmpBod

    return listbodu

def vzdalenostMeziDvema2DBody(bod1: list[float], bod2: list[float]) -> float:
    del1 = bod1[0] - bod2[0]
    del2 = bod1[1] - bod2[1]
    vysledekSq = (del1*del1) + (del2*del2) 
    vysledek = math.sqrt(vysledekSq)

    return vysledek

def vratBoundingProEdges(edgesList):
    x_max = edgesList[0].verts[0].co[0]
    x_min = edgesList[0].verts[0].co[0]
    y_max = edgesList[0].verts[0].co[1]
    y_min = edgesList[0].verts[0].co[1]
    for edge in edgesList:
        if edge.verts[0].co[0] > x_max:
            x_max = edge.verts[0].co[0]
        if edge.verts[0].co[0] < x_min:
            x_min = edge.verts[0].co[0]
        if edge.verts[1].co[0] > x_max:
            x_max = edge.verts[1].co[0]
        if edge.verts[1].co[0] < x_min:
            x_min = edge.verts[1].co[0]
        if edge.verts[0].co[1] > y_max:
            y_max = edge.verts[0].co[1]
        if edge.verts[0].co[1] < y_min:
            y_min = edge.verts[0].co[1]
        if edge.verts[1].co[1] > y_max:
            y_max = edge.verts[1].co[1]
        if edge.verts[1].co[1] < y_min:
            y_min = edge.verts[1].co[1]
    listBoundingBox = (x_max, x_min, y_max, y_min)
    return listBoundingBox

def odsad (vektorBase: list[float], vektorSmerOrig: list[float], osaRoviny: int, vzdalenost: float) -> list[float]:
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
    vzdalenost = vzdalenostNejOsa(vektorSmer, vzdalenost)
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

def smerovyVektor(vektorBase: list[float], vektorSmer: list[float]) -> list[float]:
    sX = vektorSmer[0] - vektorBase[0]
    sY = vektorSmer[1] - vektorBase[1]
    sZ = vektorSmer[2] - vektorBase[2]
    vysledek = [sX, sY, sZ]
    return vysledek
    
def pripoctiNejOsa(vektorBase: list[float], vektorSmer: list[float], vzdalenost: float) -> list[float]:

    vzdalenost = vzdalenostNejOsa(vektorSmer, vzdalenost)

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

def vzdalenostNejOsa(vektorSmer: list[float], vzdalenost: float) -> float:
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
    
def vzdalenostMeziDvemaBody(bod1: list[float], bod2: list[float]) -> float:
    del1 = bod1[0] - bod2[0]
    del2 = bod1[1] - bod2[1]
    del3 = bod1[2] - bod2[2]
    vysledekSq = (del1*del1) + (del2*del2) + (del3*del3)
    vysledek = math.sqrt(vysledekSq)

    return vysledek

def vratBodMeziDvemaBody(bod1: list[float], bod2: list[float]) -> list[float]:
    vysledek = [0.0,0.0,0.0]
    vysledek[0] = (bod1[0] + bod2[0])/2
    vysledek[1] = (bod1[1] + bod2[1])/2
    vysledek[2] = (bod1[2] + bod2[2])/2
    return vysledek

def rotaceDvaBody(obj, point1, point2):
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
    return

def pripoctiY(vektorBase: list[float], vzdalenost: float) -> list[float]:
    posunutyBod = [vektorBase[0],vektorBase[1] + vzdalenost,vektorBase[2]]
    return posunutyBod

def pripoctiX(vektorBase: list[float], vzdalenost: float) -> list[float]:
    posunutyBod = [vektorBase[0] + vzdalenost,vektorBase[1],vektorBase[2]]
    return posunutyBod

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
    textInch = zaokrouhlNa(textInch, self.pocetDesetMist)
    vysledek = ''
    if context.scene.DIMENSION.showUnits == True:
        vysledek = str(foot) + 'ft ' + textInch + 'in'
    else:
        vysledek = str(foot) + '\' ' + textInch + '\"'
    return vysledek

def zaokrouhlNa(text: str, pocet: int) -> str:
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

def makeInches(self, context, KotaNumber) -> str:
    #nejdriv cele cislo pro foot a float pro inch
    inch = 0.0
    inch = KotaNumber / 0.0254
    #if math.isclose(inch,12,abs_tol = 0.00001) == True:
        #inch = 0.0
    textInch = ''
    textInch = str(round(inch, self.pocetDesetMist))
    textInch = zaokrouhlNa(textInch, self.pocetDesetMist)
    vysledek = ''
    if context.scene.DIMENSION.showUnits == True:
        vysledek = textInch + ' in'
    else:
        vysledek = textInch + '\"'
    return vysledek

def vymenTeckuZaCarku(text: str) -> str:
    vysledek = ''
    for i in text:
        if i == '.':
            vysledek = vysledek + ','
        else:
            vysledek = vysledek + i
    return vysledek

def vymenCarkuZaTecku(text: str) -> str:
    vysledek = ''
    for i in text:
        if i == ',':
            vysledek = vysledek + '.'
        else:
            vysledek = vysledek + i
    return vysledek

def vratPosledniEdge(meshObject) -> int:
    counter = 0
    for edges in meshObject.edges:
        counter += 1
    return counter

def srovnejRotationEulerObjektum(self, objekt1, objekt2, listVeci): #objekt1 bude mit rotace jako objekt2 a stred mezi body 0 a 1 v listVeci
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
    stredKotyBB = vratBodMeziDvemaBody(listVeci[0], listVeci[1]) #stred koty uvnitr objektu
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
#vzalenost uz je spocitana na nejvetsi abs osu, odsadi jakoze kolmo v ose osaRoviny na vektorSmerOrig od vektorBase
def odsad (vektorBase: list[float], vektorSmerOrig: list[float], osaRoviny: int, vzdalenost: float) -> list[float]:
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
    vzdalenost = vzdalenostNejOsa(vektorSmer, vzdalenost)
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

def textToDrawReDraw(self):
    if self.currentState == 0:
        self.textToDraw = 'select first point of dimension | snaping to edges middle is ' + self.edgesMiddleText + ' - switch with M | continue mode is ' + self.continueModeText + ' - switch with C'
    if self.currentState == 1:
        self.textToDraw = 'select second point of dimension | (un)lock world axis with X, Y, Z keys | specify length with number keys directly | snaping to edges middle is ' + self.edgesMiddleText + ' - switch with M | continue mode is ' + self.continueModeText + ' - switch with C'
    if self.currentState == 2:
        self.textToDraw = 'move bottom lines with mouse scroll | specify distance from base with mouse, or directly with number keys | snaping to edges middle is ' + self.edgesMiddleText + ' - switch with M | continue mode is ' + self.continueModeText + ' - switch with C'

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

def vratJednotkyZCisla(text: str) -> str:
    vysledek = ""
    for character in text:
        if character.isalpha():
            vysledek = vysledek + character
        if character == '\'' or character == '\"':
            vysledek = vysledek + character
    return vysledek

def vratCisloJakoTextZeStringuImp(text: str) -> str:
    vysledek = ""
    for character in text:
        if character.isnumeric() or character == ',' or character == '.':
            vysledek = vysledek + character
        elif character == "\'" or character == "t":
            vysledek = vysledek + ' '
    return vysledek    

def stringFtInToInches(text: str) -> float:
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

def vratPocetDesetinychMist(text: str) -> int:
    pocetDesetMist = 0
    afterSwitch = False
    for character in text:
        if afterSwitch == True:
            pocetDesetMist = pocetDesetMist + 1
        if character == ',' or character == '.':
            afterSwitch = True
    return pocetDesetMist

def vratCisloJakoTextZeStringu(text: str) -> str:
    vysledek = ""
    for character in text:
        if character.isnumeric() or character == ',' or character == '.':
            vysledek = vysledek + character
    return vysledek 

def indetifyText(self, context, objectTextu, objectKoty, meshKoty, typeTmp) -> bool:
    self.textSize = objectTextu.data.size
    textKoty = vymenCarkuZaTecku(objectTextu.data.body)
    jednotky = vratJednotkyZCisla(textKoty)
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
        textKoty = vratCisloJakoTextZeStringuImp(textKoty) #mezi foot a inch mezera
    else:
        textKoty = vratCisloJakoTextZeStringu(textKoty)
    self.pocetDesetMist = vratPocetDesetinychMist(textKoty)
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
        cisloKoty = stringFtInToInches(textKoty) #cislo koty je v inches
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
    vzalenostBaseBodu = vzdalenostMeziDvemaBody(meshKoty.vertices[tmpBod1].co,meshKoty.vertices[tmpBod2].co)
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