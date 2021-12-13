from Deadline.Plugins import *
from System.Diagnostics import *

def GetDeadlinePlugin():
    '''
    Get instance of this plugin
        - DEADLINEPLUGIN
    '''
    return CrCustomFfmpegConvert()

def CleanupDeadlinePlugin(deadlinePlugin):
    '''
    Clean up this plugin
    '''
    deadlinePlugin.Cleanup()

class CrCustomFfmpegConvert(DeadlinePlugin):
    '''
    Define this plugin
    '''
    def __init__(self):
        '''
        Initialize this plugin
        '''
        self.InitializeProcessCallback+=self.InitializeProcess
        self.RenderExecutableCallback+=self.RenderExecutable
        self.RenderArgumentCallback+=self.RenderArgument
    def Cleanup():
        '''
        Clean up this plugin
        '''
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback

        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
    def InitializeProcess(self):
        '''
        Initialize this process
        '''
        self.SingleFramesOnly=False
        self.PluginType=PluginType.Simple

        self.ProcessPriority=ProcessPriorityClass.BelowNormal
        self.UseProcessTree=True
        self.StdoutHandling=True
        self.PopupHandling=True

        self.AddStdoutHandlerCallback("WARNING:.*").HandleCallback+=self.HandleStdoutWarning
        self.AddStdoutHandlerCallback("ERROR:(.*)").HandleCallback+=self.HandleStdoutError

        self.AddPopupIgnorer("Popup 1")
        self.AddPopupIgnorer("Popup 2")

        self.AddPopupHandler("Popup 3","OK")
        self.AddPopupHandler("Popup 4","Do not ask me this again;continue")
    def HandleStdoutWarning(self):
        '''
        Handle warning message
        '''
        self.LogWarning(self.GetRegexMatch(0))
    def HandleStdoutError(self):
        '''
        Handle error message
        '''
        self.FailRender("Detected on error: "+self.GetRegexMatch(1))
    def RenderExecutable(self):
        '''
        Executable file to run for this render
            - get from CONFIGURATION
        '''
        executable=self.GetConfigEntry("CrCustomFfmpegConvertExecutable")
        self.LogStdout("Executable: "+executable)
        return executable
    def RenderArgument(self):
        '''
        Arguments to use for executable file
            - can get settings from OPTIONS file
        '''
        arguments=" -i {FILEA} -vcodec h264 -acodec mp2 {FILEB}".format(FILEA=self.GetPluginInfoEntry("InputFile"),FILEB=self.GetPluginInfoEntry("OutputFile"))
        self.LogStdout("Arguments: "+arguments)
        return arguments

