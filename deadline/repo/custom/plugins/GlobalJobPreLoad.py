import os
import re
import sys
from functools import partial

from System import *
from System.IO import *

from Deadline.Scripting import *
from Deadline.Slaves import *
from FranticX.Diagnostics import *


MAP = [
    ('JobPriority', 'DEADLINE_PRIORITY'),
    ('JobId', 'DEADLINE_JOBID'),
    ('JobInterruptible', 'DEADLINE_INTERRUPTABLE')
]


def AlterCommandLine(executable, arguments, workingDirectory, plugin, version, prefix):
    print("Entering Command Line Hook")

    customplug={
        "PDGDeadlinePlugin":"HoudiniPlugin",
        "CrCustomHoudinifxScript":"HoudiniFXPlugin",
        "CrCustomMayaScript":"MayaBatchPlugin"
    }

    for k,v in customplug.items():
        # check for custom plugin
        if k==plugin:
            plugin=v
            break

    if plugin == "MayaBatchPlugin" or plugin == "MayaCmdPlugin":
        app_name = "Maya"
    elif plugin == "MayaGUIPlugin":
        app_name = "MayaGUI"
    elif plugin == "HoudiniPlugin":
        app_name = "Houdini"
    elif plugin == "HoudiniFXPlugin":
        app_name = "HoudiniFX"
    elif plugin == "NukePlugin" or plugin == "NukePyPlugin":
        app_name = "Nuke"
    elif plugin == "PythonPlugin":
        app_name = "Python"
    else:
        app_name = None

    if app_name:
        app_version = version

        # Quotes the executable if it wasn't already quoted, to ensure it gets passed as a single arg
        if not executable.startswith('"') and not executable.startswith("'"):
            executable = '"{}"'.format(executable)

        os.environ["PROCESS_APP_NAME"] = str(app_name)
        os.environ["PROCESS_APP_VERSION"] = str(app_version)
        os.environ["PROCESS_APP_VARIANT"] = "regular"
        os.environ["PROCESS_BATCH_MODE"] = "1"
        os.environ["PROCESS_START_MODE"] = "execute"

        if arguments:
            arguments = executable + " " + arguments
        else:
            arguments = executable

        executable = prefix

        print "-----Modified Command Line-----"
        print " Executable: '{}'".format(executable)
        print "  Arguments: '{}'".format(arguments)
        print "Working Dir: '{}'".format(workingDirectory)
        print "-------------------------------"

    # return the original or modified exe, args, workingDir even if pipeline not available
    return (executable, arguments, workingDirectory)

def __main__(deadlinePlugin):

    deadlinePlugin.LogInfo("Setting environment (GlobalJobPreLoad)...")

    job = deadlinePlugin.GetJob()

    for item in MAP:
        data = getattr(job, item[0])
        deadlinePlugin.SetProcessEnvironmentVariable(item[1], str(data))


    pname = deadlinePlugin.__class__.__name__
    accepted_plugins = ["MayaBatchPlugin",
                        "MayaCmdPlugin",
                        "NukePlugin",
                        "NukePyPlugin",
                        "HoudiniPlugin",
                        "PythonPlugin",
                        "PDGDeadlinePlugin",
                        "CrCustomHoudinifxScript",
                        "CrCustomMayaScript"]
    accept_alter = True if pname in accepted_plugins else False

    if accept_alter:
        # depending on OS, we return global valid file path to the pipeline launch bootstrap script
        prefix = None
        process_bat = "Q:/deploy/process.bat"
        if sys.platform.startswith("win"):
            if os.path.isfile(process_bat):
                prefix = process_bat
            else:
                print("Pipeline file not found: '{}'. Failing task...".format(process_bat))
                deadlinePlugin.FailRender(
                    "Pipeline file not found: '{}'".format(process_bat))
        else:
            print("Unrecognized platform '{}'. No prefix will be added.".format(sys.platform))

        if prefix:
            pver = deadlinePlugin.GetPluginInfoEntry("Version")
            deadlinePlugin.DebugLogging = True  # optional, can be commented out
            deadlinePlugin.ModifyCommandLineCallback += lambda exe, args, wdir: AlterCommandLine(
                exe, args, wdir, pname, pver, prefix)
