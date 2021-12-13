'''
This script export abc files from the scene with materialName attribute
'''
import maya.cmds as cmds
import maya.mel as mel
import os
from tinydb import TinyDB, Query


def create_export_string(objects):
    '''
    Export root paramteer aswell, it would be lowest path of all objects
    '''
    filtered_list = []
    exportString = ''
    for object in objects:

        if cmds.objExists(object):

            shapes = cmds.listRelatives(object,  path=True, shapes=True)
            if shapes:
                for shape in shapes:

                    if(cmds.objectType(shape) == "mesh"):
                        if (cmds.getAttr(shape+".intermediateObject") == 0):
                            modified_name = "-root " + \
                                cmds.ls(object, l=True)[0]
                            #print object + "    " + shape + "    "+ str(cmds.polyEvaluate(shape, v=True))
                            filtered_list.append(shape)
                            exportString += modified_name + " "

    # return exportString
    return filtered_list


def create_materialName_parameter(ref_file, shapes):
    for shape in shapes:
        shadingEngine = cmds.listConnections(shape, type="shadingEngine")
        shader = ref_file + "/" + \
            cmds.listConnections(
                shadingEngine[0] + ".surfaceShader")[0].split(":")[-1]

        if (cmds.attributeQuery("materialName", node=shape, ex=True) == False):
            cmds.addAttr(shape, ln="materialName", dt="string")
        cmds.setAttr(shape+".materialName", shader, type="string")


def export_scene(selRefNodes=[]):
    db = TinyDB('c:/temp/db.json')
    db.purge()
    start = cmds.playbackOptions(q=True, min=True)
    end = cmds.playbackOptions(q=True, max=True)
    refNodes = cmds.ls(type="reference")
    refEnvNodes = []
    ref_list = []
    if len(selRefNodes) > 0:
        refNodes = selRefNodes

    for node in refNodes:

        if node.find("UNKNOWN_REF_NODE") == -1:
            if node.find("sharedReferenceNode") == -1:

                name_split = node.split(":")
                ref_namespace = name_split[-1]
                # print ref_namespace + "   " + node
                #ref_namespace = node
                if ref_namespace.startswith("ttv_prop") or ref_namespace.startswith("ttv_envint"):

                    # get reference path
                    ref_fullname = cmds.referenceQuery(
                        node, filename=True, unresolvedName=True)
                    if ref_fullname.endswith("}"):
                        ref_fullname = ref_fullname[:-3]

                    # create shader package path
                    shader_package_file = os.path.basename(ref_fullname).split(
                        "/")[-1].split(".")[0].rstrip("_MASTER")
                    if shader_package_file.split("_")[-1].startswith("v"):
                        l = len(shader_package_file.split("_")[-1])
                        shader_package_file = shader_package_file[:-l-1]
                    shader_package_path = os.path.dirname(
                        ref_fullname) + "/shaderExport/"

                    ref_content = cmds.referenceQuery(
                        node, nodes=True, dp=True)
                    export_objects = create_export_string(ref_content)
                    print "nesta" + node
                    if export_objects:

                        create_materialName_parameter(
                            shader_package_file, export_objects)

                        cmds.select(export_objects)

                        fullname = cmds.file(q=True, sn=True)
                        dirname = os.path.dirname(fullname)

                        abc_file = dirname.rstrip(
                            "anim/maya")+"/_Export/Crater/"+ref_namespace+".abc"

                        export_string = 'AbcExport -j "-frameRange ' + str(start) + ' ' + str(
                            end) + ' -stripNamespaces -attrPrefix materialName -uvWrite -writeColorSets -writeFaceSets -worldSpace -writeVisibility -writeUVSets -dataFormat ogawa -sl -file ' + abc_file + '"'
                        os.mkdir(dirname.rstrip("anim/maya")+"/_Export/Crater/")
                        print ref_namespace + "   " + shader_package_file + \
                            "    " + shader_package_path + "    " + ref_fullname
                        ref_list.append({"ref_node": ref_namespace, "abc_file": abc_file, "ref_file": ref_fullname,
                                         "shader_path": shader_package_path, "shader_package": shader_package_file})
                        db.insert({"ref_node": ref_namespace, "abc_file": abc_file, "ref_file": ref_fullname,
                                   "shader_path": shader_package_path, "shader_package": shader_package_file})
                        mel.eval(export_string)
    return ref_list
