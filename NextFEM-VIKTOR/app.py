# coding=windows-1252
import math, json
import viktor as vkt
from viktor.parametrization import (ViktorParametrization, NumberField, ColorField, Text, GeometrySelectField, BooleanField, SetParamsButton)
from viktor import ViktorController, UserMessage
from viktor.geometry import (SquareBeam, Material, Extrusion, Color, Group, LinearPattern, Point, RectangularExtrusion, Line,
                             BidirectionalPattern, Sphere, Triangle, TriangleAssembly)
from viktor.views import GeometryView, GeometryResult
from viktor.external.generic import GenericAnalysis
from viktor.core import File
from pathlib import Path

class Parametrization(ViktorParametrization):
    text1 = Text("## NextFEM model \n"
        "**Adjust the node size**")
    Nradius = NumberField("Node size", variant='slider', min=1, max=20, default=2)
    reloadModel = BooleanField("reloadModel",visible=False)
    reloadModelButt = SetParamsButton("Reload model", "getNFmodel")
    Selected=GeometrySelectField('Select entity')

class Controller(ViktorController):
    label = "NextFEM model viewport"
    parametrization = Parametrization

    def getNFmodel(self, params, **kwargs):
        # Note that executable_key matches the config.yaml of the worker
        generic_analysis = GenericAnalysis(
            files=[('get-model.py', File.from_path(Path(__file__).parent / "get-model.py"))], 
            executable_key="get_model", 
            output_filenames=["model.json","results.json"]
        )
        generic_analysis.execute(timeout=300)
        output_file = generic_analysis.get_output_file("model.json", as_file=True)
        modelD= (output_file.getvalue(encoding='windows-1252')); # json.loads
        output_file = generic_analysis.get_output_file("results.json", as_file=True)
        results= (output_file.getvalue(encoding='windows-1252')); # json.loads
        # loads model in storage
        vkt.Storage().set('model',data=vkt.File.from_data(modelD), scope='entity')
        vkt.Storage().set('results',data=vkt.File.from_data(results), scope='entity')
        return vkt.SetParamsResult({"reloadModel": True})

    def getRGBfromI(self,RGBint):
        blue =  RGBint & 255
        green = (RGBint >> 8) & 255
        red =   (RGBint >> 16) & 255
        return red, green, blue
    
    @GeometryView("3D building", duration_guess=2, x_axis_to_right=True)
    def get_geometry(self, params, **kwargs):
        nodes=[]; elems=[]; nfmodel=""
        # from storage
        if 'model' in vkt.Storage().list(scope='entity'):
            file = vkt.Storage().get('model', scope='entity')
            nfmodel=json.loads(file.getvalue())

        if nfmodel=="":
            print("Nothing to draw"); return GeometryResult([Group(nodes),Group(elems)])
        # Create nodes
        node_material = Material("Node", color=Color.viktor_blue())
        node_radius = params.Nradius/20
        nfnodes={}

        for n in nfmodel['nodes']:
            nfnodes[n['num']]=Point(n['X'], n['Y'], n['Z'])
            nodes.append(Sphere(centre_point=nfnodes[n['num']],radius=node_radius,
                                         material=node_material,identifier=n['num']))
        
        # dictionary of sections
        nfsect={}
        nfScolor={}
        for s in nfmodel['sects']:
            nfsect[s['ID']]=s
            red,green,blue = self.getRGBfromI(int(s['col']))
            nfScolor[s['ID']]=Material("s" + str(s['ID']), color=Color(red,green,blue))
        # dictionary of materials
        nfmat={}
        for m in nfmodel['materials']:
            nfmat[m['ID']]=m

        # Create elements
        nfelems={}
        for e in nfmodel['elems']:
            nfelems[e['num']]=e
            if e['type']==1:
                # get section points
                pts=[]
                pts1=nfsect[int(e['sect'])]['fillPoints'][0]
                for p in pts1:
                    pts.append(Point(p['X'],p['Y']))
                b=Extrusion(pts,Line(nfnodes[e['n'][0]],nfnodes[e['n'][1]]),material=nfScolor[int(e['sect'])],identifier=e['num'])
                elems.append(b)
            elif e['type']==2:
                # TRIA: get section for thickness
                thk=nfsect[int(e['sect'])]['thickness']
                t1=Triangle(nfnodes[e['n'][0]],nfnodes[e['n'][1]],nfnodes[e['n'][2]])
                t1=Triangle(nfnodes[e['n'][2]],nfnodes[e['n'][1]],nfnodes[e['n'][0]])
                t=TriangleAssembly([t1,t2],material = nfScolor[int(e['sect'])],skip_duplicate_vertices_check=True,identifier=e['num']);
                elems.append(t)
                # edges
                elems.append(Line(nfnodes[e['n'][0]],nfnodes[e['n'][1]]))
                elems.append(Line(nfnodes[e['n'][1]],nfnodes[e['n'][2]]))
                elems.append(Line(nfnodes[e['n'][2]],nfnodes[e['n'][0]]))
            elif e['type']==3:
                # QUAD: get section for thickness
                thk=nfsect[int(e['sect'])]['thickness']
                t1=Triangle(nfnodes[e['n'][0]],nfnodes[e['n'][1]],nfnodes[e['n'][2]])
                t2=Triangle(nfnodes[e['n'][0]],nfnodes[e['n'][2]],nfnodes[e['n'][3]])
                t3=Triangle(nfnodes[e['n'][2]],nfnodes[e['n'][1]],nfnodes[e['n'][0]])
                t4=Triangle(nfnodes[e['n'][3]],nfnodes[e['n'][2]],nfnodes[e['n'][0]])
                q=TriangleAssembly([t1,t2,t3,t4], skip_duplicate_vertices_check=True,identifier=e['num'])
                elems.append(q)
                # edges
                elems.append(Line(nfnodes[e['n'][0]],nfnodes[e['n'][1]]))
                elems.append(Line(nfnodes[e['n'][1]],nfnodes[e['n'][2]]))
                elems.append(Line(nfnodes[e['n'][2]],nfnodes[e['n'][3]]))
                elems.append(Line(nfnodes[e['n'][3]],nfnodes[e['n'][0]]))
            else:
                pass

        # info about selected entity
        if params.Selected:
            if params.Selected in nfelems:
                info=""
                e=nfelems[params.Selected]
                info+="Connectivity: " + str(e['n']) + '\n'
                if ('lun' in e and e['lun']>0): info+="Beam length="+str(e['lun']) + '\n'
                print(info); # show in dev log

        return GeometryResult([Group(nodes),Group(elems)])
    
    @vkt.TableView("Reactions")
    def table_view(self, params, **kwargs):
        data=[]
        if 'results' in vkt.Storage().list(scope='entity'):
            nfres=""
            file = vkt.Storage().get('results', scope='entity')
            nfres=json.loads(file.getvalue())
            for lc in nfres['results']:
                for dt in lc['DataSet']:
                    for rr in dt['react']:
                        data.append([rr['ID'], lc['LCname'], dt['time'], rr['x'], rr['y'], rr['z'], rr['rx'], rr['ry'], rr['rz']])

        return vkt.TableResult(data,column_headers=["Node", "LC", "time", "RX", "RY", "RZ", "RrX", "RrY", "RrZ"])
    
    @vkt.TableView("Section properties")
    def sects_view(self, params, **kwargs):
        data=[]
        if 'model' in vkt.Storage().list(scope='entity'):
            nfmodel=""
            file = vkt.Storage().get('model', scope='entity')
            nfmodel=json.loads(file.getvalue())
            for s in nfmodel['sects']:
                data.append([s['ID'], s['name'], s['Area'], s['Jxc'], s['Jyc'], s['Jxyc'], s['xc'], s['yc']])

        return vkt.TableResult(data,column_headers=["ID", "Name", "Area", "Jx", "Jy", "Jxy", "Center X", "CenterY"])