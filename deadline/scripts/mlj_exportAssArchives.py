import os
import sys

import pymel.core as pm
import maya.cmds as cmds

import maya.standalone
maya.standalone.initialize()



def mlj_exportAssArchives():

    #Set FPS to 25
    if not cmds.currentUnit (query=True, time= True) == 'pal':
        cmds.currentUnit(time="pal")

    #Create export folder
    fullPath = cmds.file(q=True, sn=True)
    char = fullPath.lstrip('Z:/PRODUCTIONS/ODP/HWP/03_3D/ASSETS/01_CHARACTERS/').split('/')[0]
    exportPath = 'Z:/PRODUCTIONS/ODP/HWP/03_3D/ASSETS/01_CHARACTERS/' + char + '/SCENE/10_ASS_EXPORT_v003'

    if not os.path.exists(exportPath):
        os.mkdir(exportPath)

    #Find anim loops dir
    animLoc = 'Z:/PRODUCTIONS/ODP/HWP/03_3D/ASSETS/01_CHARACTERS/crowd/SCENE/06_ALEMBIC/' + char + '/forExport'

    animationClips = []

    for (_, _, filenames) in os.walk(animLoc):
        animationClips.extend(filenames)

    #Find characters and props
    charNode = []
    propList = []
    for obj in cmds.ls(assemblies=True):
        if obj.startswith('E_char'):
            charNode.append(obj)   
        
        if obj.startswith('E_prop'):
            propList.append(obj)
            
        if obj.startswith('E_phone'):
            phoneNode = obj
            
        if obj.startswith('E_stick'):
            stickNode = obj
    charRefNode=""
    for character in charNode:
        if not "_reference" in character:
            charRefNode = cmds.referenceQuery(character, referenceNode=True)

    phoneRefNode = cmds.referenceQuery(phoneNode, referenceNode=True) 
    stickRefNode = cmds.referenceQuery(stickNode, referenceNode=True) 

    #Export standins
    for animClip in animationClips:

        print("Anim Clip: {}".format(animClip))

        clipName = animClip.split('_')[1]
        animClipPath = exportPath + '/' + clipName

        #Export character standins
        if animClip.split("_")[2] == 'body':
            
            #change alembic ref
            cmds.file(animLoc + '/' + animClip, loadReference=charRefNode)

            #find character alembic
            allAlembicObjects = cmds.ls(type='AlembicNode')
            charAlembicNode = ''
            for abcO in allAlembicObjects:
                
                if abcO.startswith('E_char'):
                    charAlembicNode = abcO
            
            startFrame = cmds.getAttr(charAlembicNode + '.startFrame')
            endFrame = cmds.getAttr(charAlembicNode + '.endFrame')

            if not os.path.exists(animClipPath):
                os.mkdir(animClipPath)
            
            charAssName = char + '_body_' + clipName + '.ass'
            pm.select(charNode)
            #Export charachivecter ar

            export_path = animClipPath + '/' + charAssName
            print("Exporting character to: {}".format(export_path))
            cmds.arnoldExportAss(selected=True, startFrame=startFrame, endFrame=endFrame, filename=export_path, cam='perspShape')
            
            for prp in propList:
                
                propAssName = char + '_' + (prp.split (":")[0].split("_")[2]) + '_' + clipName + '.ass'
                pm.select(prp)

                export_path = animClipPath + '/' + propAssName
                print("Exporting prop to: {}".format(export_path))
                cmds.arnoldExportAss(selected=True, startFrame=startFrame, endFrame=endFrame, filename=export_path, cam='perspShape')
                
        #Export phone prop standins       
        if animClip.split("_")[2] == 'phone':
            
            cmds.file(animLoc + '/' + animClip, loadReference = phoneRefNode)
            
            #find phone alembic
            allAlembicObjects = cmds.ls(type='AlembicNode')
            phoneAlembicNode = ''
            for abcPhone in allAlembicObjects:
                
                if abcPhone.startswith('E_phone'):
                    phoneAlembicNode = abcPhone
                    
            startFrame = cmds.getAttr(phoneAlembicNode + '.startFrame')
            endFrame = cmds.getAttr(phoneAlembicNode + '.endFrame')
            
            if not os.path.exists(animClipPath):
                os.mkdir(animClipPath)
                
            phoneAssName = char + '_phone_' + clipName + '.ass'
            for obj in cmds.ls(assemblies=True):
                if obj.startswith('E_phone'):
                    phoneNode = obj
            pm.select(phoneNode)
            #Export charachivecter ar

            export_path = animClipPath + '/' + phoneAssName
            print("Exporting phone to: {}".format(export_path))
            cmds.arnoldExportAss(selected=True, startFrame=startFrame, endFrame=endFrame, filename=export_path, cam='perspShape')

        #Export stick prop standins   
        if animClip.split("_")[2] == 'stick':
            
            cmds.file(animLoc + '/' + animClip, loadReference=stickRefNode)
            
            #find stick alembic
            allAlembicObjects = cmds.ls(type='AlembicNode')
            stickAlembicNode = ''
            for abcStick in allAlembicObjects:
                
                if abcStick.startswith('E_stick'):
                    stickAlembicNode = abcStick
                    
            startFrame = cmds.getAttr(stickAlembicNode + '.startFrame')
            endFrame = cmds.getAttr(stickAlembicNode + '.endFrame')
            
            if not os.path.exists(animClipPath):
                os.mkdir(animClipPath)
                
            stickAssName = char + '_stick_' + clipName + '.ass'
            for obj in cmds.ls(assemblies=True):
                if obj.startswith('E_stick'):
                    stickNode = obj

            pm.select(stickNode)
            #Export charachivecter ar

            export_path = animClipPath + '/' + stickAssName
            print("Exporting stick to: {}".format(export_path))
            cmds.arnoldExportAss(selected=True, startFrame=startFrame, endFrame=endFrame, filename=export_path, cam='perspShape')

    print('  ********  DONE!  ********  ') 


def open_maya_scene(path):
    # open scene
    print("Opening: {}".format(path))
    pm.openFile(path, force=True)

def reset_maya_scene():
    # reset scene
    print("Done.")
    print("Closing scene...")
    pm.newFile(force=True)

def main():
    maya_file = sys.argv[1]

    if not os.path.isfile(maya_file):
        print("ERROR: File does not exist {}".format(maya_file))
    
    print("Opening maya file...")
    open_maya_scene(maya_file)

    print("Setting verbosity...")
    if not cmds.objExists("defaultArnoldRenderOptions"):
        print("SCRIPT: defaultArnoldRenderOptions does not exists in scene.")
    else:
        cmds.setAttr("defaultArnoldRenderOptions.log_verbosity", 0)

    print("Executing process...")
    mlj_exportAssArchives()

    print("Closing maya file...")
    reset_maya_scene()

    print("Exiting mayapy...")
    sys.exit(0)

if __name__ == "__main__":
    main()
