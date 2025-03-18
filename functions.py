import math
import mathutils # type: ignore

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