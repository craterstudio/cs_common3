import hou
from tinydb import TinyDB, Query
import _alembic_hom_extensions as abc
from . import cr_dt_shader_assigments_from_attr


def importAbc():
    db=TinyDB('c:/temp/db.json')
    pos=[0,0]
    for item in db:
        abc_file=item["abc_file"]
        ref_node=item["ref_node"]
        
        print abc_file
        root = hou.node('obj')
        alembic = root.createNode('alembicarchive', node_name=ref_node)
        
        alembic.setPosition(pos)
        pos=pos[0], pos[1]-1
        parameter = alembic.parm('fileName')
        parameter.set(abc_file)
        
        alembic.parm('buildHierarchy').pressButton()
        cr_dt_shader_assigments_from_attr.shader_assigment_from_attr([alembic])