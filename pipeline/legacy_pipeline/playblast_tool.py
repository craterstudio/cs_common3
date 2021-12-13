## PLAYBLAST SCRIPT

import os
import re
import sys
import shutil
import subprocess

from Qt import QtCore
from Qt import QtGui
from Qt import QtCompat
from Qt.QtWidgets import (
    QWidget, QGridLayout, QLabel, QCheckBox, QLineEdit, QComboBox, QPushButton)

from legacy_pipeline import pipeline_tools

try:
    #Maya imports
    import maya.cmds as cmds
    import pymel.core as pc
    from pymel.core import *
    import maya.OpenMaya as OpenMaya
    import maya.OpenMayaUI as OpenMayaUI
    import maya.mel
except:
    #Houdini imports
    import hou

WINDOW_NAME = "pbWindow"


def to_bool(value):
    valid = {'true': True, 't': True, '1': True,
             'false': False, 'f': False, '0': False,
             }

    if isinstance(value, bool):
        return value

    if not isinstance(value, basestring):
        raise ValueError('invalid literal for boolean. Not a string.')

    lower_value = value.lower()
    if lower_value in valid:
        return valid[lower_value]
    else:
        raise ValueError('invalid literal for boolean: "%s"' % value)

def playblastCrater(rootnode, artist_name, exact_name, fn_elements, fn_optional, desc, dl_force, task, mask, maskRatio, slate):

    #GET SCENE INFO
    rootnode.update()
    dirname=rootnode.path
    file=rootnode.filename
    file_no_ver=rootnode.filename_no_ext
    production=rootnode.production
    project=rootnode.project
    ver = rootnode.ver

    if ver == "":
        ver = "v0000"
    
    if fn_optional != '':
        file=file_no_ver+fn_optional+"_"+ver
    else:
        file=file_no_ver+ver   

    playblast_template="Y:/PRODUCTIONS/"+production+"/"+project+"/04_COMP/01_SHARED/06_PLAYBLAST_TEMPLATE/playblast_template_photojpeg.nk"

    if os.path.isfile(playblast_template)==False:
       playblast_template = "Q:/resources/nuke/templates/playblast_template_photojpeg.nk"

    start=rootnode.start
    end=rootnode.end
    if rootnode.app=='maya':
        qt_start=start
        qt_end=end
        width=cmds.getAttr("defaultResolution.width")
        height=cmds.getAttr("defaultResolution.height")
    else:
        qt_start=start
        qt_end=end
    
    try:
        maskRatio=float(maskRatio)
    except:
        maskRatio=2.35      

    # check if slate is checked
    if slate == True:
        firstFrame = start - 1
    else:
        firstFrame = start
        
    # check for sound files
    try:
        aPlayBackSliderPython = maya.mel.eval('$tmpVar=$gPlayBackSlider')
        active_audio_node = cmds.timeControl(aPlayBackSliderPython, query=True, sound=True)

        soundFilename = cmds.getAttr(active_audio_node + ".filename")
        soundOffsetMaya =  cmds.getAttr(active_audio_node + ".offset")
        soundOffset = int(start)-int(soundOffsetMaya)
        soundOffset = -soundOffset
        soundInScene = True
    except:
        soundInScene = False

       

       
    # Create review folder
    try:
        os.stat(dirname+"/03_REVIEW")
    except:
        os.mkdir(dirname+"/03_REVIEW")
    try:
        os.stat(dirname+"/03_REVIEW/tmp")
    except:
        os.mkdir(dirname+"/03_REVIEW/tmp")

    playblast_file=dirname+"/03_REVIEW/tmp/"+file+"_tmp"
    final_playblast_file = dirname + "/03_REVIEW/" + file + ".mov"

    if rootnode.app=='maya':
        view = OpenMayaUI.M3dView.active3dView()
        cam = OpenMaya.MDagPath()
        view.getCamera(cam)
        camPath = cam.fullPathName()
        cmds.select(camPath)
        camera=(camPath.split("|"))[-1]

        if (cmds.objectType(camPath) == "camera"):
            cameraShape=camPath
            camera = cmds.listRelatives(camPath, p=True)[0]   
        else:
            cameraShape=cmds.listRelatives(camPath,s=True)[0]
        
        overscan=cmds.getAttr(str(cameraShape)+".overscan")
        cmds.setAttr((cameraShape+".overscan"), 1)
        movie=cmds.playblast(st=start,et=end,v=False,fo=True,f=playblast_file,os=True,fp=4, format="image",compression="JPG",qlt=100, p=100, w=width, h=height)
        print "maya playblast:" + movie
        movie_dir=dirname+"/03_REVIEW/tmp/"
        cmds.setAttr((cameraShape+".overscan"), overscan)
    else:
        import toolutils
        
        def viewname(viewer):
            viewname = {
                'desktop' : viewer.pane().desktop().name(),
                'pane' : viewer.name(),
                'type' :'world',
                'viewport': viewer.curViewport().name()
            }
            return '{desktop}.{pane}.{type}.{viewport}'.format(**viewname)


        def viewwrite(options='', outpath='ip'):
            current_view = viewname(toolutils.sceneViewer())
            hou.hscript('viewwrite {} {} {}'.format(options, current_view, outpath))

        houdini_playblast_file=dirname+"/03_REVIEW/tmp/"+file+"_tmp."+"'$F4'"+".jpg"
        movie_dir=dirname+"/03_REVIEW/tmp/"
        viewwrite('-q 4 -f '+str(start)+' '+str(end), houdini_playblast_file)
        movie=houdini_playblast_file.replace("'$F4'","####")

    #create nuke script inside 
    #check if playblast template exist

    src = playblast_template
    dst = dirname + "/03_REVIEW/" + file + ".nk"

    nuke_file_template=open(src,"r")
    nuke_file_cont=nuke_file_template.read()

    nuke_file_cont=nuke_file_cont.replace(" luts {", (" frame "+str(firstFrame)+"\n"+" first_frame "+str(firstFrame)+"\n"+" last_frame "+str(end)+"\n"+" luts {"))
    nuke_file_cont=nuke_file_cont.replace("Read_QT",("Read_QT\n"+' file '+movie.replace("\\","/"))+'\n frame_mode "start at"\n frame '+str(start)+"\n first "+str(qt_start)+"\n last "+str(qt_end)+"\n origfirst "+str(qt_start)+"\n origlast "+str(qt_end))
    nuke_file_cont=nuke_file_cont.replace("Write {", ("Write {\n"+' file '+final_playblast_file))
    nuke_file_cont=nuke_file_cont.replace("CutLength {{last_frame-first_frame}}", ("CutLength {{last_frame-first_frame}}"+"\n SlateFrame "+str(start-1)))
    nuke_file_cont=nuke_file_cont.replace('UserName ""', 'UserName "'+artist_name+'"')
    nuke_file_cont=nuke_file_cont.replace('Task anim', 'Task ' + task)
    nuke_file_cont=nuke_file_cont.replace('Slate_Notes ""', 'Slate_Notes "'+ str(desc)+'"')
    nuke_file_cont=nuke_file_cont.replace('use_original_filename true','use_original_filename '+ str(exact_name).lower()) 
    nuke_file_cont=nuke_file_cont.replace('"client name: " T CRATER','"client name: " T '+ production)
    nuke_file_cont=nuke_file_cont.replace('CB_Guides false','CB_Guides '+ str(mask).lower())
    nuke_file_cont=nuke_file_cont.replace('ratio 2.35','ratio '+ str(maskRatio))
    
    #if there is sound file
    if soundInScene == True:
        nuke_file_cont=nuke_file_cont.replace(" name Write_QT", (' mov32_audiofile "' + soundFilename+'"\n'+' mov32_audio_offset ' + str(int(soundOffset))+'\n'+' mov32_units Frames'+'\n'+' mov64_audiofile "' + soundFilename+'"\n'+' mov64_audio_offset ' + str(int(soundOffset))+'\n'+' mov64_units Frames\n' + " name Write_QT"))
                                
    nuke_file_template.close()
    nuke_file=open(dst,"w")
    nuke_file.write(nuke_file_cont)
    nuke_file.close()

    #execute render of nuke script
    if dl_force == False:
        if os.path.isfile("c:/Program Files/Nuke11.1v3/Nuke11.1.exe"):
            nuke_install=True
        else:
            nuke_install=False
            os.remove(dst)
            print("Please install Nuke, or use Deadline")

        if nuke_install==True:
            sys.stdout.write("Prerendering playblast in Nuke..." + "\n")

            process_dot_bat = os.environ.get("PROCESS_BAT")

            if not os.path.isfile(process_dot_bat):
                print("process.bat not found")
            else:
                if rootnode.app == "maya":
                    new_env = os.environ.copy()
                    new_env["PYTHONHOME"] = ""
                    new_env["PROCESS_APP_NAME"] = "Nuke"
                    new_env["PROCESS_APP_VERSION"] = "11.1v3"
                    new_env["PROCESS_APP_VARIANT"] = "regular"
                    new_env["PROCESS_BATCH_MODE"] = "1"
                    new_env["PROCESS_START_MODE"] = "run"
                    proc = subprocess.check_output(('\"' + process_dot_bat + '\" -F ' + str(
                        firstFrame) + "-" + str(end) + " -x " + dst.replace("/", "\\")), env=new_env, shell=True)
                    print(proc)
                else:
                    new_env = os.environ.copy()
                    # TODO(Sale): calling exact version of nuke is wrong, calling it without environment setup is even worse
                    # make this better
                    new_env["PYTHONHOME"] = ""
                    new_env["PROCESS_APP_NAME"] = "Nuke"
                    new_env["PROCESS_APP_VERSION"] = "11.1v3"
                    new_env["PROCESS_APP_VARIANT"] = "regular"
                    new_env["PROCESS_BATCH_MODE"] = "1"
                    new_env["PROCESS_START_MODE"] = "run"
                    proc = subprocess.Popen([process_dot_bat, "-F",
                                            str(firstFrame) + "-" + str(end), "-x", dst], env=new_env, shell=True, stdout=subprocess.PIPE, bufsize=1)
                    # proc = subprocess.Popen(["c:/Program Files/Nuke11.1v3/Nuke11.1.exe", "-F",
                    #     str(firstFrame) + "-" + str(end), "-x", dst], env=new_env, shell=True, stdout=subprocess.PIPE, bufsize=1)

                    for line in iter(proc.stdout.readline, b''):
                        print line,
                    proc.communicate()

                filename = os.path.basename(movie).replace(".####.jpg", "")
                pattern = filename + "[^\\d].*jpg$"
                for root, dirs, files in os.walk(movie_dir):
                    for file in filter(lambda x: re.match(pattern, x), files):
                        os.remove(os.path.join(root, file))

                os.remove(dst)
                os.rmdir(movie_dir)
                sys.stdout.write("Successfully rendered playblast: " + final_playblast_file)
                os.startfile(final_playblast_file)
    else:
        deadline_job_info=open("Q:/resources/deadline/presets/playblast/job_info.txt","r")
        deadline_job_info_cont=deadline_job_info.read()
        deadline_job_info_cont=deadline_job_info_cont.replace("Frames=1-1000", ("Frames="+str(firstFrame)+"-"+str(end)))
        deadline_job_info_cont=deadline_job_info_cont.replace('Name=""', 'Name='+file)
        deadline_job_info_cont=deadline_job_info_cont.replace('ChunkSize=1000', 'ChunkSize='+str((end-start)*2))
        deadline_job_info_cont=deadline_job_info_cont.replace('PostJobScript=""','PostJobScript='+dirname+"/03_REVIEW/postscript_"+file+".py")
        deadline_job_info_cont=deadline_job_info_cont.replace('OutputFilename0=""','OutputFilename0='+final_playblast_file)
        deadline_job_info_cont=deadline_job_info_cont.replace('OutputDirectory0=""','OutputDirectory0='+dirname+"/03_REVIEW/")
        deadline_job_info.close()
        deadline_job_info_tmp_file=dirname+"/03_REVIEW/job_info.txt"
        deadline_job_plugin_info_file = "Q:/resources/deadline/presets/playblast/plugin_info_v03.txt"
        deadline_job_info_tmp=open(deadline_job_info_tmp_file,"w")
        deadline_job_info_tmp.write(deadline_job_info_cont)
        deadline_job_info_tmp.close()
        deadline_post_script='import os\nimport shutil\n'+'from Deadline.Scripting import *\n'+'def __main__( *args ):\n'+' try:\n'+'  shutil.rmtree("'+movie_dir.replace("\\","/")+'")\n'+'  os.remove("'+dirname+"/03_REVIEW/job_info.txt"+'")\n'+'  os.remove("'+dst+'")\n'+' except:\n'+'  print "Windows cant find file"'
        deadline_post_script_file=open((dirname+"/03_REVIEW/postscript_"+file+".py"),"w")
        deadline_post_script_file.write(deadline_post_script)
        deadline_post_script_file.close()
        cmd = ('deadlinecommand ' + deadline_job_info_tmp_file + " " + deadline_job_plugin_info_file + " " + dst.replace("/", "\\"))
        print cmd

        subprocess.check_output(cmd, shell=True)
        sys.stdout.write("Successfully submitted to Deadline, file will be: " + final_playblast_file + "\n")


class pbWindow(QWidget):

    def __init__(self):
        super(pbWindow, self).__init__()

        self.scene_root = None

        ### settings
        self.settings_path = os.path.join(
            os.getenv('HOME'), "settingsFile.ini")

        ### build ui
        self.initUI()

    def initUI(self):

        self.scene_root = pipeline_tools.Scene_root()
        self.scene_root.update()

        ### detects if script is run from Maya
        if self.scene_root.app == 'maya':
            from maya import OpenMayaUI as omui 
            omui.MQtUtil.mainWindow()    
            ptr = omui.MQtUtil.mainWindow()    
            mainWindow = QtCompat.wrapInstance(long(ptr), QWidget)
            self.setParent(mainWindow)
        if self.scene_root.app=='houdini':
            self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
            self.setParent(hou.ui.mainQtWindow(), QtCore.Qt.Window)
            self.setStyleSheet(hou.qt.styleSheet())
            self.setProperty("houdiniStyle", True)

        ### configures the main window
        self.setWindowFlags(QtCore.Qt.Window)
        self.resize(320, 240)
        self.setWindowTitle('Playblast options')
        layout=QGridLayout(self)
        layout.setRowMinimumHeight(1,5)
        layout.setRowMinimumHeight(3,5)
        layout.setRowMinimumHeight(5,5)

        # Create a label and display it all together
        artistLabel = QLabel(self)
        artistLabel.setText('Artist name:')
        artistLabel.setIndent(20)
        layout.addWidget(artistLabel,0,0)

        self.artistInput = QLineEdit(self)
        layout.addWidget(self.artistInput,0,1)

        #optional fields
        optionalLabel = QLabel(self)
        optionalLabel.setText('Optional string:')
        optionalLabel.setIndent(20)
        layout.addWidget(optionalLabel,2,0)
    
        self.optionalInput = QLineEdit(self)
        layout.addWidget(self.optionalInput,2,1)
        self.optionalInput.show()
    
        #description fields
        descLabel = QLabel(self)
        descLabel.setText('Description:')
        descLabel.setIndent(20)
        layout.addWidget(descLabel,4,0)
    
        self.descInput = QLineEdit(self)
        layout.addWidget(self.descInput,4,1)

        #use deadline
        self.udCheckbox=QCheckBox(self)
        self.udCheckbox.setText('Use deadline')
        layout.addWidget(self.udCheckbox,6,0)
    
        #use exact name
        self.enCheckbox=QCheckBox(self)
        self.enCheckbox.setText('Use exact name')
        layout.addWidget(self.enCheckbox,6,1)
        
        #Mask enable
        self.maskCheckbox=QCheckBox(self)
        self.maskCheckbox.setText('Mask')
        layout.addWidget(self.maskCheckbox,7,0)    

        #Mask ratio
        self.maskRatioBox = QLineEdit(self)
        self.maskRatioBox.setText("2.35")
        layout.addWidget(self.maskRatioBox,7,1)
        
        #Slate enable
        self.slateCheckbox=QCheckBox(self)
        self.slateCheckbox.setText('Slate')
        layout.addWidget(self.slateCheckbox,8,0)    
        
        #combo box
        self.taskCombo=QComboBox(self)
        taskItems=['anim','anim_blocking','anim_depthtest','anim_matte','anim_test','Postviz','matchmove','CMM','Layout','Lookdev','sim']
        self.taskCombo.addItems(taskItems)
        i_task=0
        if self.scene_root.task in taskItems:
            i_task = taskItems.index(self.scene_root.task)
        self.taskCombo.setCurrentIndex(i_task)

        layout.addWidget(self.taskCombo,8,1)

        ### add buttons
        okButton = QPushButton("Ok")
        okButton.clicked.connect(self.okPressed)
        layout.addWidget(okButton,9,0)
        cancelButton=QPushButton("Cancel")
        cancelButton.clicked.connect(self.cancelPressed)
        layout.addWidget(cancelButton,9,1)



        ### get settings file if exists
        if os.path.exists(self.settings_path):
            settings_obj = QtCore.QSettings(
                self.settings_path, QtCore.QSettings.IniFormat)
            
            if WINDOW_NAME in settings_obj.childGroups():
                self.artistInput.setText(
                    settings_obj.value(WINDOW_NAME + "/artistInput"))
                self.optionalInput.setText(
                    settings_obj.value(WINDOW_NAME + "/optionalInput"))
                self.descInput.setText(
                    settings_obj.value(WINDOW_NAME + "/descInput"))
                self.udCheckbox.setChecked(
                    to_bool(settings_obj.value(WINDOW_NAME + "/udCheckbox")))
                self.enCheckbox.setChecked(
                    to_bool(settings_obj.value(WINDOW_NAME + "/enCheckbox")))
                self.maskCheckbox.setChecked(
                    to_bool(settings_obj.value(WINDOW_NAME + "/maskCheckbox")))
                try:
                    self.slateCheckbox.setChecked(
                        to_bool(settings_obj.value(WINDOW_NAME + "/slateCheckbox")))
                except:
                    self.slateCheckbox.setChecked(True)

        else:
            self.enCheckbox.setChecked(True)
            self.slateCheckbox.setChecked(True)

    def okPressed(self):
        self.close()

        globalArtist = self.artistInput.displayText()
        globalUseExactName = self.enCheckbox.isChecked()
        filename_format = '111111'
        globalOptional = self.optionalInput.displayText()
        globalDescription = self.descInput.displayText()
        globalUseDeadline = self.udCheckbox.isChecked()
        globalTask = self.taskCombo.currentText()
        globalMask = self.maskCheckbox.isChecked()
        globalMaskRatio = self.maskRatioBox.displayText()
        globalSlate = self.slateCheckbox.isChecked()

        playblastCrater(self.scene_root, globalArtist, globalUseExactName, filename_format, globalOptional,
                        globalDescription, globalUseDeadline, globalTask, globalMask, globalMaskRatio, globalSlate)

    def cancelPressed(self):
        self.close()

    def closeEvent(self, event):
        # self.pickParameters()

        settings_obj = QtCore.QSettings(
            self.settings_path, QtCore.QSettings.IniFormat)

        settings_obj.setValue(WINDOW_NAME + "/artistInput", self.artistInput.displayText())
        settings_obj.setValue(WINDOW_NAME + "/optionalInput", self.optionalInput.displayText())
        settings_obj.setValue(WINDOW_NAME + "/descInput", self.descInput.displayText())
        settings_obj.setValue(WINDOW_NAME + "/udCheckbox", self.udCheckbox.isChecked())
        settings_obj.setValue(WINDOW_NAME + "/enCheckbox", self.enCheckbox.isChecked())
        settings_obj.setValue(WINDOW_NAME + "/maskCheckbox", self.maskCheckbox.isChecked())
        settings_obj.setValue(WINDOW_NAME + "/slateCheckbox", self.slateCheckbox.isChecked())

        event.accept()

def playblastCrater_WIN():
    playblastWindow = pbWindow()
    playblastWindow.show()