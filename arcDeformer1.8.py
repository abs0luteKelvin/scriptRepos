##--------------------------------------------------------------------------
##
## ScriptName : arcEdgeLoop
## Author     : Joe Wu
## URL        : http://im3djoe.com
## LastUpdate : 2021/01/13
##            : create one bezier curve for selected edge loop, smooth edge loop with 2~5 control point and dropoff slider
## Version    : 1.0  First version for public test
##            : 1.1  snap to curve option, support full circle
##            : 1.2  new plan ,making nurbs option, support snap to curve / even space with full circle /
##            : 1.3  fixing bugs
##            : 1.4  rename function to avoid problem with unBevel and semiCircle
##            : 1.5  still bug with circle bezier Curve
##            : 1.6  added arcMode
##            : 1.7  fixing bug when edge loop in a full circle
##            : 1.71 add to viewport even in isolate mode
##            : 1.72 add mutli curve, fix value change when switch between curve type
##            : 1.8  add attach costum curve
##
## Other Note : test in maya 2020.2 windows
##
## Install    : copy and paste script into a python tab in maya script editor
## bug        : bezier curve with full circle lose shape when convert from open curve to close curve
##--------------------------------------------------------------------------

import maya.cmds as mc
import maya.mel as mel
import math

def arcDeformer():
    if mc.window("arcDeformerUI", exists = True):
        mc.deleteUI("arcDeformerUI")
    arcDeformerUI = mc.window("arcDeformerUI",title = "arcDeformer 1.8", w=320)
    mc.frameLayout(labelVisible= False)
    mc.rowColumnLayout(nc=4 ,cw=[(1,5),(2,60),(3,20),(4,180)])
    mc.text(l ='')
    mc.text(l ='Curve Type')
    mc.text(l ='')
    mc.radioButtonGrp('curveType', nrb=2, sl=1, labelArray2=['Bezier', 'Nurbs'], cw = [(1,100),(2,100)],cc='controlNumberSwitch()')
    mc.setParent( '..' )
    mc.rowColumnLayout(nc=10 ,cw=[(1,10),(2,60),(3,20),(4,50),(5,10),(6,50),(7,10),(8,50),(9,10),(10,95)])
    mc.text(l ='')
    mc.text(l ='Options')
    mc.text(l ='')
    mc.checkBox('makeArc', label= "Arc" ,v = 1, cc ='makeArcSwitch()')
    mc.text(l ='')
    mc.checkBox('snapCurve', label= "Snap" ,v = 1, cc = 'disableEvenSpaceCheckBox()')
    mc.text(l ='')
    mc.checkBox('evenSpace', label= "Even" ,v = 1)
    mc.text(l ='')
    mc.checkBox('cleanCurve', label= "Keep Curve" ,v = 1)
    mc.setParent( '..' )
    mc.intSliderGrp('CPSlider', cw3=[80, 30, 180], label = 'Control Point ',  field= 1, min= 2, max= 10, fmx = 500, v = 3 )
    mc.floatSliderGrp('dropOffSlider' , label = 'DropOff', v = 0.01, cw3=[80, 30, 180], field=1 ,pre = 2, min= 0.01, max= 10)
    mc.rowColumnLayout(nc=4 ,cw=[(1,120),(2,80),(3,10),(4,80)])
    mc.text(l ='')
    mc.button( l= 'Run',  c= 'arcEdgeLoop()')
    mc.text(l ='')
    mc.button( l= 'Done',  c= 'arcDone()')
    mc.text(l ='')
    mc.setParent( '..' )
    mc.showWindow(arcDeformerUI)


def arcDone():
    global storeEdge
    global currentArcCurve
    if mc.objExists('arcCurve*'):
        arcCurveList = mc.ls( "arcCurve*", transforms =1  )
        a = arcCurveList[0]
        for a in arcCurveList:
            if 'BaseWire' not in a:
                shapeNode = mc.listRelatives(a, fullPath=True )
                hist = mc.listConnections(mc.listConnections(shapeNode[0],sh=1, d=1 ) ,d=1 ,sh=1)
                mc.delete(hist,ch=1)
        mc.delete('arcCurve*')
    if len(currentArcCurve)>0:
        if mc.objExists(currentArcCurve):
            shapeNode = mc.listRelatives(currentArcCurve, fullPath=True )
            hist = mc.listConnections(mc.listConnections(shapeNode[0],sh=1, d=1 ) ,d=1 ,sh=1)
            mc.delete(hist,ch=1)
    if mc.objExists(currentArcCurve):
        mc.select(currentArcCurve)
    mc.select(storeEdge,add=1)
    if mc.objExists(currentArcCurve + 'BaseWire'):
        mc.delete(currentArcCurve + 'BaseWire')

def arcEdgeLoop():
    global storeEdge
    global currentArcCurve
    currentDropOff = mc.floatSliderGrp('dropOffSlider' ,q=1,v=1)
    snapCheck = mc.checkBox('snapCurve',q = 1 ,v = 1)
    goEven = mc.checkBox('evenSpace', q=1 ,v = 1)
    conP = mc.intSliderGrp('CPSlider',q=1 , v = True )
    curveT = mc.radioButtonGrp('curveType', q=1, sl=1)
    goArc = mc.checkBox('makeArc', q=1 ,v = 1)
    cClean = mc.checkBox('cleanCurve', q=1 ,v = 1)
    selEdge = mc.filterExpand(expand=True ,sm=32)
    selCurve = mc.filterExpand(expand=True ,sm=9)
    if selCurve:
        if len(selEdge)>0 and len(selCurve)== 1:
            storeEdge = selEdge
            mc.select(selCurve,d=1)
            selMeshForDeformer = mc.ls(sl=1,o=1)
            getCircleState,listVtx = vtxLoopOrderCheck()
            newCurve = mc.duplicate(selCurve[0], rr=1)
            mc.rename(newCurve[0],'newsnapCurve')
            currentArcCurve = 'newsnapCurve'
            mc.rebuildCurve(currentArcCurve,ch=1, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s = 100, d=1, tol=0.01)
            #check tip order
            curveTip = mc.pointOnCurve(currentArcCurve , pr = 0, p=1)
            tipA = mc.pointPosition(listVtx[0],w=1)
            tipB = mc.pointPosition(listVtx[-1],w=1)
            distA = math.sqrt( ((tipA[0] - curveTip[0])**2)  + ((tipA[1] - curveTip[1])**2)  + ((tipA[2] - curveTip[2])**2) )
            distB = math.sqrt( ((tipB[0] - curveTip[0])**2)  + ((tipB[1] - curveTip[1])**2)  + ((tipB[2] - curveTip[2])**2) )
            if distA > distB:
                listVtx.reverse()
            #snap to curve
            if goEven == 1:
                for q in range(len(selEdge)+1):
                    if q == 0:
                        pp = mc.pointOnCurve(currentArcCurve , pr = 0, p=1)
                        mc.move( pp[0], pp[1], pp[2],listVtx[q] , a =True, ws=True)
                    else:
                        pp = mc.pointOnCurve(currentArcCurve , pr = (1.0/len(selEdge)*q), p=1)
                        mc.move( pp[0], pp[1], pp[2],listVtx[q] , a =True, ws=True)
            else:
                sum = 0
                totalEdgeLoopLength = 0
                Llist = []
                uList = []
                pList = []
                for i in range(len(listVtx)-1):
                    pA = mc.pointPosition(listVtx[i], w =1)
                    pB = mc.pointPosition(listVtx[i+1], w =1)
                    checkDistance = math.sqrt( ((pA[0] - pB[0])**2)  + ((pA[1] - pB[1])**2)  + ((pA[2] - pB[2])**2) )
                    Llist.append(checkDistance)
                    totalEdgeLoopLength = totalEdgeLoopLength + checkDistance

                for j in Llist:
                    sum = sum + j
                    uList.append(sum)
                for k in uList:
                    p = k / totalEdgeLoopLength
                    pList.append(p)

                for q in range(len(selEdge)+1):
                    if q == 0:
                        pp = mc.pointOnCurve(currentArcCurve , pr = 0, p=1)
                        mc.move( pp[0], pp[1], pp[2],listVtx[q] , a =True, ws=True)
                    else:
                        pp = mc.pointOnCurve(currentArcCurve , pr = pList[q-1], p=1)
                        mc.move( pp[0], pp[1], pp[2],listVtx[q] , a =True, ws=True)
            mc.delete('newsnapCurve')
            deformerNames  = mc.wire(selMeshForDeformer, gw=0, en = 1, ce = 0, li= 0, dds = [(0,1)], dt=1, w = selCurve[0])
            mc.connectControl("dropOffSlider", (deformerNames[0]+".dropoffDistance[0]"))
            if snapCheck == 0:
                mc.setAttr((deformerNames[0] + '.dropoffDistance[0]'),1)
            else:
                mc.setAttr((deformerNames[0] + '.dropoffDistance[0]'),currentDropOff)
            currentArcCurve = selCurve[0]
            mc.select(selCurve[0])
    else:
        if selEdge:
            storeEdge = selEdge
            if cClean == 0:
                if mc.objExists('arcCurve*'):
                    arcDone()
            selMeshForDeformer = mc.ls(sl=1,o=1)
            getCircleState,listVtx = vtxLoopOrderCheck()
            deformerNames = []
            #make nurbs curve
            if getCircleState == 0: #Arc
                if goArc == 1:
                    midP = int(len(listVtx)/2)
                    mc.move(0.01, 0, 0,selEdge[midP],r=1, cs=1 ,ls=1, wd =1)
                    p1 = mc.pointPosition(listVtx[0], w =1)
                    p2 = mc.pointPosition(listVtx[midP], w =1)
                    p3 = mc.pointPosition(listVtx[-1], w =1)
                    newNode = mc.createNode('makeThreePointCircularArc')
                    mc.setAttr((newNode + '.pt1'), p1[0],  p1[1] , p1[2])
                    mc.setAttr((newNode + '.pt2'), p2[0],  p2[1] , p2[2])
                    mc.setAttr((newNode + '.pt3'), p3[0],  p3[1] , p3[2])
                    mc.setAttr((newNode + '.d'), 3)
                    mc.setAttr((newNode + '.s'), len(listVtx))
                    newCurve = mc.createNode('nurbsCurve')
                    mc.connectAttr((newNode+'.oc'), (newCurve+'.cr'))
                    mc.delete(ch=1)
                    transformNode = mc.listRelatives(newCurve, fullPath=True , parent=True )
                    mc.select(transformNode)
                    mc.rename(transformNode,'arcCurve0')
                    getNewNode = mc.ls(sl=1)
                    currentArcCurve = getNewNode[0]
                    numberP = 0
                    if curveT == 2:#nubs curve
                        numberP = int(conP) - 3
                        if numberP < 1:
                            numberP = 1
                    else:
                        numberP = int(conP) -1
                    mc.rebuildCurve(currentArcCurve,ch=1, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s= numberP, d=3, tol=0.01)
                else:
                    p1 = mc.pointPosition(listVtx[0], w =1)
                    mc.curve(d= 1, p=p1)
                    mc.rename('arcCurve0')
                    getNewNode = mc.ls(sl=1)
                    currentArcCurve = getNewNode[0]
                    for l in range(1,len(listVtx)):
                        p2 = mc.pointPosition(listVtx[l], w =1)
                        mc.curve(currentArcCurve, a= 1, d= 1, p=p2)
                    numberP = int(conP) -1
                    mc.rebuildCurve(currentArcCurve,ch=1, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s= numberP, d=1, tol=0.01)
            else: #circle
                p1 = mc.pointPosition(listVtx[0], w =1)
                mc.curve(d= 1, p=p1)
                mc.rename('arcCurve0')
                getNewNode = mc.ls(sl=1)
                currentArcCurve = getNewNode[0]
                for l in range(1,len(listVtx)):
                    p2 = mc.pointPosition(listVtx[l], w =1)
                    mc.curve(currentArcCurve, a= 1, d= 1, p=p2)
                mc.curve(currentArcCurve, a= 1, d= 1, p=p1)
                mc.closeCurve(currentArcCurve,ch=0, ps=2, rpo=1, bb= 0.5, bki=0, p=0.1)
                conP = mc.intSliderGrp('CPSlider',q=1 , v = True )
                numberP = int(conP)
                if numberP < 4:
                    numberP = 4
                    mc.intSliderGrp('CPSlider',e=1 , v = 4 )
                mc.rebuildCurve(currentArcCurve,ch=1, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s = numberP, d=3, tol=0.01)
                ###########################################################################
            mc.delete(currentArcCurve ,ch=1)
            totalEdgeLoopLength = 0;
            sum = 0
            Llist = []
            uList = []
            pList = []
            #mc.select(selEdge)
            for i in selEdge:
                e2v =mc.polyListComponentConversion(i,fe=1, tv=1)
                e2v = mc.ls(e2v,fl=1)
                pA = mc.pointPosition(e2v[0], w =1)
                pB = mc.pointPosition(e2v[1], w =1)
                checkDistance = math.sqrt( ((pA[0] - pB[0])**2)  + ((pA[1] - pB[1])**2)  + ((pA[2] - pB[2])**2) )
                Llist.append(checkDistance)
                totalEdgeLoopLength = totalEdgeLoopLength + checkDistance
            if goEven == 1:
                avg = totalEdgeLoopLength / (len(selEdge))
                for j in range(len(selEdge)):
                    sum = ((j+1)*avg)
                    uList.append(sum)
            else:
                for j in Llist:
                    sum = sum + j
                    uList.append(sum)
            for k in uList:
                p = k / totalEdgeLoopLength
                pList.append(p)
            #snap to curve
            if snapCheck == 1:
                for q in range(len(pList)):
                    if q+1 == len(listVtx):
                        pp = mc.pointOnCurve(currentArcCurve, pr = 0, p=1)
                        mc.move( pp[0], pp[1], pp[2],listVtx[0] , a =True, ws=True)
                    else:
                        pp = mc.pointOnCurve(currentArcCurve , pr = pList[q], p=1)
                        mc.move( pp[0], pp[1], pp[2],listVtx[q+1] , a =True, ws=True)
            #convert to Bezier Curve
            mc.delete(currentArcCurve ,ch=1)
            mc.select(currentArcCurve)
            if curveT == 1:
                mc.nurbsCurveToBezier()
                if getCircleState == 1: #circle need to fix bug
                    mc.closeCurve(currentArcCurve,ch=0, ps=2, rpo=1, bb= 0.5, bki=0, p=0.1)
                    mc.closeCurve(currentArcCurve,ch=0, ps=2, rpo=1, bb= 0.5, bki=0, p=0.1)
            #wireWrap
            deformerNames  = mc.wire( selMeshForDeformer, gw=0, en = 1, ce = 0, li= 0, dds = [(0,1)], dt=1, w = currentArcCurve)
            #select controllers
            if getCircleState == 0:
                mc.setToolTo('moveSuperContext')
                degree = mc.getAttr(currentArcCurve + '.degree')
                spans = mc.getAttr(currentArcCurve + '.spans')
                numberCVs = degree + spans
                collect = []
                for x in range(int(numberCVs/3)-1):
                    g = currentArcCurve + '.cv[' + str((x+1)*3) + ']'
                    collect.append(g)
                mc.select(collect ,r=1)

            else:
                mc.select(currentArcCurve + '.cv[*]')
            cmd = 'doMenuNURBComponentSelection("' + currentArcCurve + '", "controlVertex");'
            mel.eval(cmd)
            mc.connectControl("dropOffSlider", (deformerNames[0]+".dropoffDistance[0]"))
            if snapCheck == 0:
                mc.setAttr((deformerNames[0] + '.dropoffDistance[0]'),1)
            else:
                mc.setAttr((deformerNames[0] + '.dropoffDistance[0]'),currentDropOff)
            #add to viewport even in isolate mode
            for x in range(1,5):
                mc.isolateSelect(('modelPanel' + str(x)), ado= currentArcCurve )

def makeArcSwitch():# min point for Nurbs are 4 point
    goArc = mc.checkBox('makeArc', q=1 ,v = 1)
    curveT = mc.radioButtonGrp('curveType', q=1, sl=1)
    if goArc == 0:
        mc.intSliderGrp('CPSlider', e=1, min= 4, v = 4 , fmx = 500)
    else:
        if curveT == 1:
            mc.intSliderGrp('CPSlider', e=1, min= 2, v = 3, fmx = 500)
        else:
            mc.intSliderGrp('CPSlider', e=1, min= 4, v = 4, fmx = 500)

def disableEvenSpaceCheckBox():
    snapCheck = mc.checkBox('snapCurve',q = 1 ,v = 1)
    if snapCheck == 0 :
        mc.checkBox('evenSpace', e=1 ,en=0)
    else:
        mc.checkBox('evenSpace', e=1 ,en=1)

def controlNumberSwitch():# min point for Nurbs are 4 point
    curveT = mc.radioButtonGrp('curveType', q=1, sl=1)
    getCurrentV = mc.intSliderGrp('CPSlider', q=1 ,v = 1 )
    if curveT == 2:
        mc.intSliderGrp('CPSlider', e=1, min= 4 )
        if getCurrentV < 4:
            mc.intSliderGrp('CPSlider', e=1, v= 4 )
    else:
        mc.intSliderGrp('CPSlider', e=1, min= 2 )

def vtxLoopOrderCheck():
    selEdges = mc.ls(sl=1,fl=1)
    shapeNode = mc.listRelatives(selEdges[0], fullPath=True , parent=True )
    transformNode = mc.listRelatives(shapeNode[0], fullPath=True , parent=True )
    edgeNumberList = []
    for a in selEdges:
        checkNumber = ((a.split('.')[1]).split('\n')[0]).split(' ')
        for c in checkNumber:
            findNumber = ''.join([n for n in c.split('|')[-1] if n.isdigit()])
            if findNumber:
                edgeNumberList.append(findNumber)
    getNumber = []
    for s in selEdges:
        evlist = mc.polyInfo(s,ev=True)
        checkNumber = ((evlist[0].split(':')[1]).split('\n')[0]).split(' ')
        for c in checkNumber:
            findNumber = ''.join([n for n in c.split('|')[-1] if n.isdigit()])
            if findNumber:
                getNumber.append(findNumber)
    dup = set([x for x in getNumber if getNumber.count(x) > 1])
    getHeadTail = list(set(getNumber) - dup)
    checkCircleState = 0
    if not getHeadTail: #close curve
        checkCircleState = 1
        getHeadTail.append(getNumber[0])
    vftOrder = []
    vftOrder.append(getHeadTail[0])
    count = 0
    while len(dup)> 0 and count < 1000:
        checkVtx = transformNode[0]+'.vtx['+ vftOrder[-1] + ']'
        velist = mc.polyInfo(checkVtx,ve=True)
        getNumber = []
        checkNumber = ((velist[0].split(':')[1]).split('\n')[0]).split(' ')
        for c in checkNumber:
            findNumber = ''.join([n for n in c.split('|')[-1] if n.isdigit()])
            if findNumber:
                getNumber.append(findNumber)
        findNextEdge = []
        for g in getNumber:
            if g in edgeNumberList:
                findNextEdge = g
        edgeNumberList.remove(findNextEdge)
        checkVtx = transformNode[0]+'.e['+ findNextEdge + ']'
        findVtx = mc.polyInfo(checkVtx,ev=True)
        getNumber = []
        checkNumber = ((findVtx[0].split(':')[1]).split('\n')[0]).split(' ')
        for c in checkNumber:
            findNumber = ''.join([n for n in c.split('|')[-1] if n.isdigit()])
            if findNumber:
                getNumber.append(findNumber)
        gotNextVtx = []
        for g in getNumber:
            if g in dup:
                gotNextVtx = g
        dup.remove(gotNextVtx)
        vftOrder.append(gotNextVtx)
        count +=  1
    if checkCircleState == 0:
        vftOrder.append(getHeadTail[1])
    else:#close curve remove connected vtx
        if vftOrder[0] == vftOrder[1]:
            vftOrder = vftOrder[1:]
        elif vftOrder[0] == vftOrder[-1]:
            vftOrder = vftOrder[0:-1]
    finalList = []
    for v in vftOrder:
        finalList.append(transformNode[0]+'.vtx['+ v + ']' )

    return checkCircleState, finalList

arcDeformer()