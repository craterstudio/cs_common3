import hou
from tinydb import TinyDB, Query
import sys
import os


def set_shader_params(shader, parameters):
 
  for parameter in parameters:
    value=parameters[parameter]
    if (isinstance(value, float)):
      shader.parm(parameter).set(value)
    if (isinstance(value, list)): 
      shader.parm(parameter+"r").set(value[0])
      shader.parm(parameter+"g").set(value[1])
      shader.parm(parameter+"b").set(value[2])
   
 

def set_shader_connections(shader, parameters):
  for parameter in parameters:
    value=parameters[parameter]
    rs_texture=shader.parent().createNode("redshift::TextureSampler", node_name=parameter)
    rs_texture.parm("tex0").set(value)
    shader.setNamedInput(parameter, rs_texture, 0)   



def create_shader_package(ref_list):
  for ref in ref_list:
    shader_db_name=ref.split("/")[-1].rstrip(".ma")
    shader_db_path=os.path.dirname(ref)
    shader_db=shader_db_path+"/shader_export/"+shader_db_name+".json"
    mat = hou.node("/mat")
    mat_nodes=mat.children()
    lowest_y = min([x.position()[1] for x in mat_nodes])
    root=mat.createNode("subnet", shader_db_name, run_init_scripts=False)
    root.setPosition([mat_nodes[0].position()[0], lowest_y -1])
    
    db=TinyDB(shader_db)
    shaders = Query()
    # Search for a field value
    for item in db:
        name=item["name"]
        type=item["type"]
        shader_params=item["params"]
        shader_connections=item["shader_connections"]
        # print shader_params["diffuse_color"]
        mat_builder=root.createNode("redshift_vopnet", node_name=name)
        shader=mat_builder.createNode("redshift::Material", node_name=name)
        sg=hou.node(mat_builder.path()+"/redshift_material1")
        sg.setFirstInput(shader)
        set_shader_params(shader, shader_params)
        set_shader_connections(shader, shader_connections)
        mat_builder.layoutChildren()
    root.layoutChildren()
    
    root.createDigitalAsset(name=shader_db_name, hda_file_name=shader_db_path+"/shader_export/"+shader_db_name+".hda" )