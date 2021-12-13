import _alembic_hom_extensions as abc
import hou

def shader_assigment_from_attr(objects):
    # sel=hou.selectedNodes()
    for node in objects:
        sub_children=node.allSubChildren()
        abcPath=hou.parm(node.path()+"/fileName").eval()
        error_objects=[]
        
        

        for child in sub_children:
            if child.type().name()=="alembic":
                path=hou.parm(child.path()+'/objectPath').eval()
                attrName='materialName'      
                materialName=abc.alembicArbGeometry(abcPath, path, attrName, hou.frame() / hou.fps())[0][0]
                try:
                    materialName="/mat/"+materialName
                    print materialName
                    parent=child.parent()
                    hou.parm(parent.path()+"/shop_materialpath").set(materialName)
                    
                except:
                    #error_objects.append(child)
                    print child.name()
                
        # print error_objects
