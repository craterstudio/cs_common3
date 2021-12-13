import os
import re
import socket

try:
    import maya.cmds as cmds
    import pymel.core as pm
    MAYA = True
except ImportError:
    MAYA = False

try:
    import hou
    HOUDINI = True
except ImportError:
    HOUDINI = False

try:
    import nuke
    NUKE = True
except ImportError:
    NUKE = False


def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]


class Scene_root(object):
    def __init__(self):
        self._setup_complete = False

        self.update()

        process_batch_mode = os.environ.get("PROCESS_BATCH_MODE", "0")

        if process_batch_mode == "0":
            print("Setting environment variables:")
            self.register_env_variables()
        else:
            print("Running in batch mode, setting environment variables disabled.")

    def update(self):
        if MAYA:
            app = "maya"
        elif HOUDINI:
            app = "houdini"
        elif NUKE:
            app = "nuke"
        else:
            print("Scene root is designed to run inside Maya, Houdini or Nuke")
            return

        self.app = app

        # get frame range info
        if self.app == "maya":
            # in case application is Maya
            fullname = cmds.file(q=True, sn=True)

            # set project first
            pm.workspace.chdir(os.path.dirname(fullname))

            # get info
            namestring = cmds.file(q=True, l=True)[0]
            self.start = int(cmds.playbackOptions(
                q=True, animationStartTime=True))
            self.end = int(cmds.playbackOptions(q=True, animationEndTime=True))
        elif self.app == "houdini":
            # in case application is Houdini
            fullname = hou.hipFile.name()
            namestring = fullname
            self.start = int(hou.playbar.playbackRange()[0])
            self.end = int(hou.playbar.playbackRange()[1])
        else:
            # in case application is Nuke
            fullname = nuke.root().name()
            namestring = fullname
            self.start = int(nuke.root()["first_frame"].value())
            self.end = int(nuke.root()["last_frame"].value())

        # Parsing of the filename elements
        file_ext = os.path.basename(fullname)
        if file_ext:
            filename, ext = os.path.splitext(file_ext)
        else:
            filename = "untitled"
            ext = "ma"
        dirname = os.path.dirname(fullname)
        dirstring = os.path.dirname(namestring)
        self.fullname = fullname
        self.basename = file_ext
        self.filename = filename
        self.ext = ext

        file_no_ver = ""
        ver = ""

        # set scene project path and type
        scene_type = None
        scene_project_path = None
        collection = None
        entity = None

        if self.app == "maya":
            namestring_split = namestring.replace("\\", "/").split("/")
            if namestring_split[-1] != "untitled":
                if len(namestring_split) > 5:
                    if namestring_split[5] == "SEQUENCES":
                        scene_type = "sequence"
                    elif namestring_split[5] == "ASSETS":
                        scene_type = "asset"
                    else:
                        scene_type = None
                else:
                    scene_type = None
                path_s = list()
                for i in range(1, 8):
                    path_s.append(namestring_split[i])
                scene_project_path = os.path.join(
                    namestring_split[0], "\\", *path_s).replace("\\", "/")

                if len(namestring_split) > 6:
                    collection = namestring_split[6]
                else:
                    collection = None

                if len(namestring_split) > 7:
                    entity = namestring_split[7]
                else:
                    entity = None
        elif self.app == "houdini":
            h_scenename = hou.hipFile.name()
            h_scenename_split = h_scenename.replace("\\", "/").split("/")
            if h_scenename != "untitled.hip":
                if len(h_scenename_split) > 5:
                    if h_scenename_split[5] == "SEQUENCES":
                        scene_type = "sequence"
                    elif h_scenename_split[5] == "ASSETS":
                        scene_type = "asset"
                    else:
                        scene_type = None
                else:
                    scene_type = None

                if len(h_scenename_split) > 10:
                    path_s = list()
                    for i in range(1, 10):
                        path_s.append(h_scenename_split[i])

                    scene_project_path = os.path.join(
                        h_scenename_split[0], "\\", *path_s).replace("\\", "/")

                if len(h_scenename_split) > 6:
                    collection = h_scenename_split[6]
                else:
                    collection = None

                if len(h_scenename_split) > 7:
                    entity = h_scenename_split[7]
                else:
                    entity = None

        self.scene_type = scene_type
        self.scene_project_path = scene_project_path

        self.collection = collection
        self.entity = entity

        # GET VERSION STRING
        for part in filename.split('_'):
            if len(part) > 0:
                if part[0] == 'v':
                    try:
                        int(part[1:])
                        ver = part
                    except:
                        file_no_ver += part+"_"
                else:
                    file_no_ver += part+"_"
            else:
                file_no_ver += part+"_"
        self.ver = ver

        # GET TASK INFO
        task = ''
        if '07_SIMULATION' in dirname:
            task = 'sim'
        elif '04_ANIMATION' in dirname:
            task = 'anim'
        elif '01_LAYOUT' in dirname:
            task = 'Layout'
        elif '15_LOOKDEV' in dirname:
            task = 'Lookdev'

        self.task = task

        # GET PDG INFO
        if self.app == 'houdini':
            host_ip = str(get_ip_address())
            houdini_version = str(hou.applicationVersion()[0]) + "." + str(hou.applicationVersion()[1])

            self.host_ip = host_ip
            self.houdini_version = houdini_version

        # get general info
        general_info = parse_info_from_path(namestring)
        for key, value in general_info.items():
            self.__dict__[key] = value

        if self.app == 'maya':
            self.renderer = cmds.getAttr(
                "defaultRenderGlobals.currentRenderer")
        
        # get renderer
        self.update_render_settings()

        # complete
        self._setup_complete = True

    def register_env_variables(self):

        attrs = vars(self)
        for key, value in attrs.iteritems():
            if isinstance(value, (basestring, int)) and not key.startswith("_"):
                value = str(value)
                upper = key.upper()
                prefix = "CRX_"
                env_var = prefix + upper
                print("\t'{}' -> '{}'".format(env_var, value))

                if self.app == 'maya':
                    # Standard scene_root variables
                    os.environ[env_var] = value

                if self.app == 'houdini':
                    # Standard scene_root variables
                    hou.hscript("setenv {} = {}".format(env_var, value))

                    # Custom houdini variables
                    if self.entity:
                        renderpath = "Y:/PRODUCTIONS/" + self.production + "/" + self.project + \
                            "/04_COMP/" + self.collection + "/" + self.entity + "/CG/FX"
                        hou.hscript("setenv {} = {}".format(
                            prefix + "RENDERPATH", renderpath))

                        abcpath = "75_DATATRANSFERS/07_HOUDINICACHE/alembicCache"
                        hou.hscript("setenv {} = {}".format(
                            prefix + "ABCPATH", abcpath))

                        cachepath = self.drive + ":/PRODUCTIONS/" + self.production + "/" + self.project + "/03_3D/SEQUENCES/" + self.collection
                        hou.hscript("setenv {} = {}".format(
                            prefix + "CACHEPATH", cachepath))

                if self.app == 'nuke':
                    # Standard scene_root variables
                    os.environ[env_var] = value

    def update_version_string(self, attr):
        if self.ver:
            if self.app == 'maya':
                current_name = cmds.getAttr(attr)

            if current_name:
                if current_name.startswith("v"):
                    ver_string = current_name.split("/")[0]
                    try:
                        int(ver_string[1:])
                        newname = current_name.replace(
                            ver_string, self.ver)
                        cmds.setAttr(attr, newname, type="string")
                    except:
                        print ""

    def update_render_settings(self):
        if self.ver:
            if self.app == 'maya':
                if self.renderer == 'arnold':
                    # init arnold nodes if not initialized
                    if not cmds.objExists("defaultArnoldDriver"):
                        from mtoa.core import createOptions
                        createOptions()

                    cmds.setAttr("defaultRenderGlobals.rv",
                                 self.ver, type="string")
                    driver = pm.PyNode('defaultArnoldDriver')
                    metadata0 = "STRING maya_file " + str(self.fullname)
                    driver.setAttr("customAttributes[0]", metadata0)

                # updates version Label - Arnold renderer
                else:
                    self.update_version_string("defaultRenderGlobals.ifp")
                    # if there is version string it will update it


def parse_info_from_path(input_path):
    general_info_dict = dict()

    drive = None
    filename_no_ver = None
    production = None
    project = None
    projectpath = None
    path = None

    if os.path.isfile(input_path):
        dirstring = os.path.dirname(input_path)
        if dirstring:
            if dirstring[1] == ":":
                drive = dirstring[0]
            else:
                print "Invalid path"

            match = re.match(r"^([a-zA-Z0-9_]+)(_v[0-9]{,3})$", os.path.basename(input_path))
            if match:
                filename_no_ver = match.group(1)

            if "/PRODUCTIONS/" in dirstring:
                production = (dirstring.replace(drive + ":/PRODUCTIONS/", "")).split("/")[0]
                project = (dirstring.replace(drive + ":/PRODUCTIONS/", "")).split("/")[1]
                projectpath = (drive + ":/PRODUCTIONS/" + production + "/" + project)

            # TOM patch
            elif "/ttv/episodes/" in dirstring:
                dirstring_splited = dirstring.split("/")
                production = "PMP"
                project = "TOM"
                project_origin = dirstring_splited[2]
                episode = dirstring_splited[4]
                projectpath = (drive + ":/projects/" + project_origin + "/episodes/" + episode)

                general_info_dict["project_origin"] = project_origin
                general_info_dict["episode"] = episode
            else:
                production = None
                project = None
                projectpath = None

            path = dirstring

    general_info_dict["drive"] = drive
    general_info_dict["filename_no_ver"] = filename_no_ver
    general_info_dict["production"] = production
    general_info_dict["project"] = project
    general_info_dict["projectpath"] = projectpath
    general_info_dict["path"] = path

    return general_info_dict
