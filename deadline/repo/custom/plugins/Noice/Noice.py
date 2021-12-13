import os
import re
from System import *
from System.Diagnostics import *
from System.IO import *

from Deadline.Plugins import *
from Deadline.Scripting import *


def GetDeadlinePlugin():
    return NoicePlugin()

def CleanupDeadlinePlugin(deadlinePlugin):
    deadlinePlugin.Cleanup()


class NoicePlugin(DeadlinePlugin):
    Version = -1.0

    def __init__(self):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.PostRenderTasksCallback += self.PostRenderTasks
        self.PreRenderTasksCallback += self.PreRenderTasks

    def Cleanup(self):
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.PostRenderTasksCallback
        del self.PreRenderTasksCallback

        # Remove the stdout handlers
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback

    def InitializeProcess(self):
        self.PluginType = PluginType.Simple
        self.SingleFramesOnly = True
        self.StdoutHandling = True
        self.AddStdoutHandlerCallback(
            ".*Error.*").HandleCallback += self.HandleStdoutError

    def RenderExecutable(self):
        version = int(self.GetPluginInfoEntry("Version"))
        exe = ""
        exeList = self.GetConfigEntry(
            "Noice_RenderExecutable_" + str(version))
        exe = FileUtils.SearchFileList(exeList)
        if(exe == ""):
            self.FailRender("Noice render executable was not found in the configured separated list \"" + exeList + "\".")

        return exe

    def RenderArgument(self):
        inputFile = self.GetPluginInfoEntryWithDefault(
            "InputFile", "")
        start_frame = self.GetStartFrame()

        renderArgument = ""

        inputPath_dir = os.path.dirname(inputFile)
        inputPath_filename = os.path.basename(inputFile)
        inputPath_cleanname = os.path.splitext(inputPath_filename)[0]
        inputPath_cleanname_noframe = inputPath_cleanname[:-4]
        inputPath_ext = os.path.splitext(inputPath_filename)[1]

        inputPath_formated = os.path.join(
            inputPath_dir, inputPath_cleanname_noframe + start_frame_string + inputPath_ext)

        inputFile = inputPath_formated

        if inputFile != "":
            inputFile = RepositoryUtils.CheckPathMapping(inputFile)
            inputFile = self.ProcessPath(inputFile)
            renderArgument += "-i \"%s\" " % inputFile

        additionalAOVs = self.GetPluginInfoEntryWithDefault("AdditionalAOVs", "")
        if additionalAOVs != "":
            additionalAOVsList = additionalAOVs.split(", ")
            for aov in additionalAOVsList:
                renderArgument += "-l \"%s\" " % aov

        outputFolder = self.GetPluginInfoEntryWithDefault("OutputFolder", "")
        outputFolder = RepositoryUtils.CheckPathMapping(outputFolder)
        outputFolder = self.ProcessPath(outputFolder)
        if (outputFolder == ""):
            self.FailRender("No output folder was specified.")

        outputPath_formated = os.path.join(
            outputFolder, inputPath_cleanname_noframe + start_frame_string + inputPath_ext)

        renderArgument += "-o \"%s\"" % outputPath_formated

        # temporary solution, tasks should be submitted as single frame only for now
        skipExisting = self.GetBooleanPluginInfoEntryWithDefault(
            "SkipExisting", False)
        if (skipExisting == True) and (os.path.exists(outputPath_formated) == True):
            self.LogStdout("File already exists.")
            self.ExitWithSuccess()

        additionalFrames = self.GetIntegerPluginInfoEntryWithDefault("AdditionalFrames", 0)
        patchRadius = self.GetPluginInfoEntryWithDefault("PatchRadius", "")
        searchRadius = self.GetPluginInfoEntryWithDefault("SearchRadius", "")
        variance = self.GetPluginInfoEntryWithDefault("Variance", "")

        if additionalFrames != "":
            renderArgument += " -ef %s" % additionalFrames

        if patchRadius != "":
            renderArgument += " -pr %s" % patchRadius

        if searchRadius != "":
            renderArgument += " -sr %s" % searchRadius

        if variance != "":
            renderArgument += " -v %s" % variance

        return renderArgument

    def ProcessPath(self, filepath):
        if SystemUtils.IsRunningOnWindows():
            filepath = filepath.replace("/", "\\")
            if filepath.startswith("\\") and not filepath.startswith("\\\\"):
                filepath = "\\" + filepath
        else:
            filepath = filepath.replace("\\", "/")
        return filepath

    def PreRenderTasks(self):
        self.LogInfo("Noice job starting...")

    def PostRenderTasks(self):
        self.LogInfo("Noice job finished.")

    def HandleStdoutError(self):
        self.FailRender(self.GetRegexMatch(0))
