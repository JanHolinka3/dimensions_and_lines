import math

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