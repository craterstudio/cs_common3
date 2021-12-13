import maya.cmds as cmds
from tinydb import TinyDB, Query
from itertools import imap
from operator import sub



### fix inversion, not good
def get_shader_params(shader, parameters_list, remap_dict=False):
    shader_params={}
    inv=False
 
    for parameter in parameters_list:
        if (remap_dict):
            parameter_remap=remap_dict[parameter][0]
            if (remap_dict[parameter][1]):
                inv=True
        else:
            parameter_remap=parameter
    
        try:
            attr=cmds.getAttr(shader+"." + parameter)[0]
        except:
            attr=cmds.getAttr(shader+"." + parameter)        
        if inv==False: 
            shader_params[parameter_remap] = attr
        else:
            if (isinstance(attr, float)):
                #shader_params[parameter_remap] = 1.0-attr
                shader_params[parameter_remap] = attr
            if (isinstance(attr, list)): 
                #shader_params[parameter_remap] = list(imap(sub, [1.0,1.0,1.0],attr[0]))
                shader_params[parameter_remap] = attr
    return shader_params

def get_shader_connections(shader, connection_list, remap_dict=False):
    shader_connections={}

    for connection in connection_list:
        if (remap_dict):
            connection_remap=remap_dict[connection][0]
            if (remap_dict[connection][1]):
                inv=True
        else:
            connection_remap=connection      
        if (cmds.listConnections(shader+"."+connection)):
            shader_connections[connection_remap] = cmds.getAttr(cmds.listConnections(shader+"."+ connection)[0]+".fileTextureName")
    return shader_connections    


    
    
def export_shaders():
    remap_dict={
        "color": ["diffuse_color",False],
        "incandescence": ["emission_color", False],
        "diffuse" :  ["diffuse_weight", False],
        "transparency" : ["opacity_color", True],
    }

    a=1.23
    isinstance(a, float)
    scene_geo=cmds.ls(g=True)
    shader_list=set()

    for geo in scene_geo:
        shading_engine=cmds.listConnections(geo,type="shadingEngine")
        if shading_engine:
            shader=cmds.listConnections (shading_engine[0] + ".surfaceShader")
            shader_list.add(shader[0])
        else:
            print (geo + " does not have a shader attached, attaching default (rs_default_shader)")
            shader="rs_default_shader" 
            shader_list.add(shader) 

    
    db = TinyDB('c:/temp/db.json')

    print "-------------"

    db.purge()



    for shader in shader_list:
        if (str(shader) is not "rs_default_shader"):
            type=cmds.objectType(shader)
        else:
            type="RedshiftMaterial"

        shader_params={}
        shader_connections={}

        if (str(type) == "RedshiftMaterial"):     
            if (shader is not "rs_default_shader"): 
                rs_parameters_list=["diffuse_color", "diffuse_weight", "diffuse_roughness", "emission_color", "emission_weight", "refl_color", "refl_weight", "refl_roughness", "refl_color", "refl_weight", "refl_roughness", "opacity_color", "overall_color"]

                shader_params=get_shader_params(shader, rs_parameters_list)
                shader_connections=get_shader_connections(shader, rs_parameters_list)      

        
        else:
            shader_params["diffuse_color"] = [0.5, 0.5, 0.5]
            shader_params["diffuse_weight"]  = 1.0
            shader_params["emission_color"] = [1, 0, 0]
            shader_params["emission_weight"] = 0
        
        if (str(type) == "lambert"): 
            # fix inversion problem firts, up up up
            # lambert_parameters_list=["color", "transparency", "incandescence"] 
            lambert_parameters_list=["color"]
            shader_params=get_shader_params(shader, lambert_parameters_list, remap_dict)
            shader_connections=get_shader_connections(shader, lambert_parameters_list, remap_dict)      

        print shader_params 
        db.insert({'name': str(shader), 'type': type, 'params': shader_params, 'shader_connections': shader_connections}) 