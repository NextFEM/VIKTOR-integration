# import requests
import os
from nextfempy import NextFEMrest

# current dir
dir = os.path.dirname(os.path.realpath(__file__))
# connects to the open instance of NextFEM Designer with REST API server plugin running on your machine
nf=NextFEMrest()

try:
    # clear model
    nf.newModel()
    # material and section
    mat=nf.addMatFromLib("C25/30"); print("Mat="+str(mat))
    cSect=nf.addCircSection(0.2)
    bSect=nf.addRectSection(0.2,0.3)
    # nodes
    n1=nf.addNode(0,0,0); n2=nf.addNode(0,0,3)
    n3=nf.addNode(3,0,0); n4=nf.addNode(3,0,3)
    n5=nf.addNode(0,3,0); n6=nf.addNode(0,3,3)
    n7=nf.addNode(3,3,0); n8=nf.addNode(3,3,3)
    # beams
    b1=nf.addBeam(n1,n2,cSect,mat); b2=nf.addBeam(n3,n4,cSect,mat)
    b3=nf.addBeam(n2,n4,bSect,mat)
    b4=nf.addBeam(n5,n6,cSect,mat); b5=nf.addBeam(n7,n8,cSect,mat)
    b6=nf.addBeam(n6,n8,bSect,mat)
    b7=nf.addBeam(n2,n6,bSect,mat); b8=nf.addBeam(n4,n8,bSect,mat)
    # restraints
    nf.setBC(n1,True,True,True,True,True,True)
    nf.setBC(n3,True,True,True,True,True,True)
    nf.setBC(n5,True,True,True,True,True,True)
    nf.setBC(n7,True,True,True,True,True,True)
    # loading
    nf.addLoadCase("sw"); nf.setSelfWeight("sw")
    nf.addLoadCase("perm"); nf.addLoadCase("var")
    # floorload type
    print(nf.setFloorLoad("floor1","perm",-2.5,0,0,1)); print(nf.setFloorLoad("floor1","var",-3,0,0,1))
    # floor plane on beams - nodes 2,4,8,6
    print("Apply loading plane: " + str(nf.addFloorPlane("floor1",2,n2,n4,n8,n6)))

    # analysis: run all loadcases and print outcome
    print(nf.RunModel())
    nf.refreshDesignerView(0,True)
    # send data
    data=nf.modeldata
    f=open(dir + r"\model.json",'w'); f.write(data); f.close()
    results=nf.modelresults
    r=open(dir + r"\results.json",'w'); r.write(results); r.close()
except:
    pass