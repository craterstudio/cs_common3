import os
import re
import socket
import pickle
import getpass

from datetime import datetime

import sgtk
from sgtk import TankError

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

        self._engine = None
        self._context = None
        self._setup_complete = False
        self._sgdata = None
        self.sgdata_file = None

        self.update()
        self._batch_mode = os.environ.get("PROCESS_BATCH_MODE", "0")

        if self.context:
            if self._batch_mode == "0":
                print("Getting SG data...")
                self._sgdata = self.get_sg_data()
                if not self._sgdata:
                    print("No SG data written to disc.")
                else:
                    print("Writing SG data to disc...")
                    self.sgdata_file = self.write_sg_data(self._sgdata)
                    print("Done.")

                print("Setting environment variables...")
                self.register_env_variables()
                print("Done.")
            else:
                print("Running in batch mode, setting environment variables disabled.")
        else:
            print("No context found, Scene_root disabled.")
            
    def update(self):
        self._engine = sgtk.platform.current_engine()
        if self._engine:
            self._context = self._engine.context
        self.initialize()

    @property
    def engine(self):
        return self._engine

    @property
    def context(self):
        return self._context

    def initialize(self):
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
            self.start = int(cmds.playbackOptions(q=True, animationStartTime=True))
            self.end = int(cmds.playbackOptions(q=True, animationEndTime=True))
        elif self.app == "houdini":
            # in case application is Houdini
            fullname = hou.hipFile.name()
            self.start = int(hou.playbar.playbackRange()[0])
            self.end = int(hou.playbar.playbackRange()[1])
        else:
            # in case application is Nuke
            fullname = nuke.root().name()
            self.start = int(nuke.root()["first_frame"].value())
            self.end = int(nuke.root()["last_frame"].value())

        # Parsing of the filename elements
        file_ext = os.path.basename(fullname)
        filename, ext = os.path.splitext(file_ext)

        self.fullname = fullname
        self.basename = file_ext
        self.filename = filename
        self.ext = ext

        # project
        self.project = None
        if self.context and hasattr(self.context, "project"):
            if self.context.project:
                self.project = self.context.project.get("name")

        # project data
        self.client_name = None
        self.client_project_name = None
        if self.project:
            query = self.context.sgtk.shotgun.find_one(
                "Project",
                [["id", "is", self.context.project["id"]]],
                ["sg_client_name", "sg_client_project_name"]
            )
            self.client_name = query.get("sg_client_name")
            self.client_project_name = query.get("sg_client_project_name")

        # scene type (asset or shot)
        self.scene_type = None
        if self.context and hasattr(self.context, "entity"):
            if self.context.entity:
                self.scene_type = self.context.entity.get("type")

        # set scene project path
        self.scene_project_path = os.path.dirname(self.fullname)

        # asset name or shot name
        self.entity = None
        if self.context and hasattr(self.context, "entity"):
            if self.context.entity:
                self.entity = self.context.entity.get("name")

        # asset type or sequence name
        self.collection = None
        if self.scene_type in ["Shot", "Asset"] and self.context:
            value_map = {
                "sg_sequence.Sequence.code": "collection",
                "sg_sequence.Sequence.sg_client_sequence_name": "client_collection_name",
                "sg_client_shot_name": "client_entity_name",
                "sg_asset_type": "collection",
                "sg_client_asset_name": "client_entity_name",
            }
            if self.scene_type == "Shot":
                query_fields = ["sg_sequence.Sequence.code", "sg_sequence.Sequence.sg_client_sequence_name", "sg_client_shot_name"]
            else:
                query_fields = ["sg_asset_type", "sg_client_asset_name"]

            query = self.context.sgtk.shotgun.find_one(
                self.scene_type,
                [["id", "is", self.context.entity["id"]],
                ["project", "is", self.context.project]],
                query_fields
            )

            for field in query_fields:
                value = query.get(field)
                if value:
                    key = value_map[field]
                    self.__dict__[key] = value

        # version
        self.ver = ""
        pattern = r"(.+)v([0-9]+)\.(\w+)$"
        match_version = re.match(pattern, self.basename)
        if match_version:
            scene_version = match_version.group(2)
            self.ver = "v{}".format(scene_version)

        # task
        self.task = None
        if self.context and hasattr(self.context, "task"):
            if self.context.task:
                self.task = self.context.task.get("name")

        # step
        self.step = None
        self.step_long = None
        if self.context and hasattr(self.context, "task"):
            if self.context.task and self.context.project:
                query = self.context.sgtk.shotgun.find_one(
                    "Task", [["id", "is", self.context.task["id"]], ["project", "is", self.context.project]], [
                        "step.Step.code",
                        "step.Step.short_name",
                    ])

                if "step.Step.code" in query:
                    self.step_long = query["step.Step.code"]

                if "step.Step.short_name" in query:
                    self.step = query["step.Step.short_name"]

        # pdg info
        host_ip = str(get_ip_address())
        self.host_ip = host_ip

        # user info
        user = None
        if self.context and hasattr(self.context, "user"):
            user = self.context.user.get("name")
        if not user:
            user = getpass.getuser()
        self.user = user

        if self.app == "maya":
            maya_version = cmds.about(version=True)
            self.app_version = maya_version
        elif self.app == "houdini":
            houdini_version = str(hou.applicationVersion()[0]) + "." + str(hou.applicationVersion()[1])
            self.app_version = houdini_version
        else:
            nuke_version = nuke.NUKE_VERSION_STRING
            self.app_version = nuke_version

        # get general info
        general_info = parse_info_from_path(self.fullname)
        for key, value in general_info.items():
            self.__dict__[key] = value

        if self.app == "maya":
            self.renderer = cmds.getAttr("defaultRenderGlobals.currentRenderer")
            self.update_render_settings()

        # complete
        self._setup_complete = True

    def register_env_variables(self):
        dataset = dict()
        
        attrs = vars(self)
        for key, value in attrs.iteritems():
            if isinstance(value, (basestring, int)) and not key.startswith("_"):
                value = str(value)
                upper = key.upper()
                prefix = "CRX_"
                env_var = prefix + upper

                print("\t'{}' -> '{}'".format(env_var, value))
                dataset[env_var] = value

        if self.app == 'maya':
            for k, v in dataset.items():
                # add scene_root attributes to environment
                os.environ[k] = v

        if self.app == 'houdini':
            for k, v in dataset.items():
                # standard scene_root variables
                hou.hscript("setenv {} = {}".format(k, v))

                # custom houdini variables
                if all([self.entity, self.project, self.collection, self.drive]):
                    renderpath = "Y:/PRODUCTIONS/" + self.project + \
                        "/04_COMP/" + self.collection + "/" + self.entity + "/CG/FX"
                    hou.hscript("setenv {} = {}".format(
                        prefix + "RENDERPATH", renderpath))

                    abcpath = "75_DATATRANSFERS/07_HOUDINICACHE/alembicCache"
                    hou.hscript("setenv {} = {}".format(
                        prefix + "ABCPATH", abcpath))

                    cachepath = self.drive + ":/PRODUCTIONS/" + self.project + "/03_3D/SEQUENCES/" + self.collection
                    hou.hscript("setenv {} = {}".format(
                        prefix + "CACHEPATH", cachepath))

        if self.app == 'nuke':
            for k, v in dataset.items():
                # add scene_root attributes to environment
                os.environ[k] = v

            for node in nuke.selectedNodes():
                node.knob("selected").setValue(False)

            # write attributes to "cr_rootnode" as text input knobs with values
            rootnode = nuke.toNode("cr_rootnode")
            if not rootnode:
                rootnode = nuke.createNode("NoOp")
                rootnode["name"].setValue("cr_rootnode")
                rootnode["tile_color"].setValue(4278214655)
                rootnode["hide_input"].setValue(True)

            nuke_remove_user_knobs(rootnode)
            for k, v in dataset.items():
                knob = nuke.String_Knob(k, k, "")
                knob.setValue(str(v))
                rootnode.addKnob(knob)

            for node in nuke.selectedNodes():
                node.knob("selected").setValue(False)

    def update_version_string(self, attr):
        if self.ver and self.app == 'maya':
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
                        print("Could not set version attribute.")

    def update_render_settings(self):
        if self.ver and self.app == 'maya':
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

    def get_sg_data(self):
        if not self.fullname:
            print("Cannot get SG data, file has not been saved...")
            return None

        # check if file has been saved, otherwise bail (except in Nuke since they
        # stupidly implemented onSave callback to execute BEFORE save, jesus christ...)
        if not os.path.isfile(self.fullname) and not NUKE:
            print("Cannot get SG data, scene file does not exist: '{}'".format(self.fullname))
            return None

        # always a special baby...
        if NUKE and self.fullname == "Root":
            print("Cannot get SG data, scene file does not exist.")
            return None

        sg_data = dict()

        # initialize variables
        engine = sgtk.platform.current_engine()
        context = engine.context
        shotgun = engine.sgtk.shotgun

        if not context or not hasattr(context, "task"):
            raise TankError("Could not get SG data, no task in context found. Will not retrieve SG data...")

        if context.task is None:
            raise TankError("Could not get SG data, task is not initiated. Will not retrieve SG data...")

        project = context.project
        task_id = context.task.get("id")
        entity_id = context.entity.get("id")
        entity_type = context.entity.get("type")

        if not task_id or not entity_id:
            raise TankError("Could not task or entity id. Will not retrieve SG data...")

        task_schema = shotgun.schema_field_read("Task")
        entity_schema = shotgun.schema_field_read(entity_type)

        task = shotgun.find_one(
            "Task",
            [["id", "is", task_id],
            ["project", "is", project]],
            task_schema.keys()
        )

        entity = shotgun.find_one(
            entity_type,
            [["id", "is", entity_id],
            ["project", "is", project]],
            entity_schema.keys()
        )

        if not all([entity, task]):
            raise TankError("Could not get SG data...")

        sg_data["task_data"] = task
        sg_data["entity_data"] = entity

        # use workfiles2, work template to build key values
        app = engine.apps.get("tk-multi-workfiles2", None)
        if not app:
            raise TankError("Could not load 'tk-multi-workfiles2' app.")

        template_name = app.get_setting("template_work")
        template = app.get_template_by_name(template_name)
        if not template:
            raise TankError("Could not get work template.")

        # get fields
        all_fields = dict()
        try:
            fields = template.validate_and_get_fields(self.fullname)

            if "version" in fields:
                version_key = template.keys["version"]
                version_formated = version_key.str_from_value(fields["version"])
                fields["version_formated"] = version_formated

            project = engine.context.project.get("name")
            fields["Project"] = project

            all_fields.update(fields)
        except Exception as err:
            print(err.message)
            raise TankError("Could not get work template fields.")

        sg_data["shotgun_data"] = all_fields
        convert_shotgun_datetime_objects(sg_data)

        return sg_data

    def write_sg_data(self, data):
        if not self.fullname:
            return

        sg_data_folder = os.path.join(os.path.dirname(self.fullname), ".sgdata")
        sg_data_file = os.path.join(sg_data_folder, os.path.splitext(
            os.path.basename(self.fullname))[0] + ".pickle").replace("\\", "/")

        if not os.path.isdir(sg_data_folder):
            os.makedirs(sg_data_folder)

        with open(sg_data_file, "wb") as f:
            pickle.dump(data, f)
            
        return sg_data_file

def parse_info_from_path(input_path):
    general_info_dict = dict()

    drive = None
    filename_no_ver = None
    project = None
    projectpath = None
    path = None

    dirstring = os.path.dirname(input_path)
    if dirstring:
        if dirstring[1] == ":":
            drive = dirstring[0]
        else:
            print("Invalid path")

        match = re.match(r"^([a-zA-Z0-9_]+)(_v[0-9]{,3})$", os.path.basename(input_path))
        if match:
            filename_no_ver = match.group(1)

        if "/PRODUCTIONS/" in dirstring:
            project = (dirstring.replace(drive + ":/PRODUCTIONS/", "")).split("/")[0]
            projectpath = (drive + ":/PRODUCTIONS/" + project)

        path = dirstring

    general_info_dict["drive"] = drive
    general_info_dict["filename_no_ver"] = filename_no_ver
    general_info_dict["projectpath"] = projectpath
    general_info_dict["path"] = path

    return general_info_dict


def nuke_remove_user_knobs(node):
    in_user_tab = False
    to_remove = []
    for n in range(node.numKnobs()):
        cur_knob = node.knob(n)
        is_tab = isinstance(cur_knob, nuke.Tab_Knob)

        # Track is-in-tab state
        if is_tab and cur_knob.name() == "User": # Tab name to remove
            in_user_tab = True
        elif is_tab and in_user_tab:
            in_user_tab = False

        # Collect up knobs to remove later
        if in_user_tab:
            to_remove.append(cur_knob)

    # Remove in reverse order so tab is empty before removing Tab_Knob
    for k in reversed(to_remove):
        node.removeKnob(k)

    # Select first tab
    node.knob(0).setFlag(0)


def convert_shotgun_datetime_objects(dict_object):
    for k, v in dict_object.items():
        if isinstance(v, dict):
            convert_shotgun_datetime_objects(v)
        else:
            if isinstance(v, datetime):
                dict_object[k] = v.strftime("%Y-%m-%d %H:%M:%S %Z%z")
