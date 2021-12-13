import os

from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *

from Deadline.Scripting import *
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

# GLOBALS
dg=None
settings = None
errors = False

def __main__( *args ):
    '''
    Main function called by deadline
    '''
    global dg
    global settings
    dg=DeadlineScriptDialog()
    dg.SetTitle("Convert simple ffmpeg one video format to another")
    dg.AddGrid()
    dg.AddControlToGrid("Label1", "LabelControl", "Input File", 0,0, "", False)
    dg.AddControlToGrid( "TextBoxInputFile", "TextControl", "", 0, 1 )
    dg.AddControlToGrid("Label2", "LabelControl", "Output File", 1,0, "", False)
    dg.AddControlToGrid( "TextBoxOutputFile", "TextControl", "", 1, 1 )
    dg.AddControlToGrid("Label5", "LabelControl", "Job Name", 4,0, "", False)
    dg.AddControlToGrid( "TextBoxJobName", "TextControl", "", 4, 1)
    dg.AddControlToGrid("Label6", "LabelControl", "Job Comment", 5,0, "", False)
    dg.AddControlToGrid( "TextBoxJobComment", "TextControl", "", 5, 1)
    dg.AddControlToGrid("Label7", "LabelControl", "Job Department", 6,0, "", False)
    dg.AddControlToGrid( "TextBoxJobDepartment", "TextControl", "", 6, 1)
    dg.AddControlToGrid("Label8", "LabelControl", "Job Pool", 7,0, "", False)
    dg.AddControlToGrid( "TextBoxJobPool", "TextControl", "", 7, 1)
    dg.AddControlToGrid("Label9", "LabelControl", "Job Secondary Pool", 8,0, "", False)
    dg.AddControlToGrid( "TextBoxJobSecondaryPool", "TextControl", "", 8, 1)
    dg.AddControlToGrid("Label10", "LabelControl", "Job Group", 9,0, "", False)
    dg.AddControlToGrid( "TextBoxJobGroup", "TextControl", "", 9, 1)
    dg.AddControlToGrid("Label11", "LabelControl", "Job Priority", 10,0, "", False)
    dg.AddControlToGrid( "TextBoxJobPriority", "TextControl", "", 10, 1)
    dg.AddControlToGrid("Label12", "LabelControl", "Job Concurrent Tasks", 11,0, "", False)
    dg.AddControlToGrid( "TextBoxJobConcurrentTasks", "TextControl", "", 11, 1)
    dg.EndGrid()
    # DONE adding text boxes
    dg.AddGrid()
    dg.AddHorizontalSpacerToGrid("DummyLabel",0,0)
    ok=dg.AddControlToGrid("OK","ButtonControl","OK",0,1,expand=False)
    ok.ValueModified.connect(OkButtonPressed)
    # REACT to ok button pressed
    cancel=dg.AddControlToGrid("CANCEL","ButtonControl","Cancel",0,2,expand=False)
    cancel.ValueModified.connect(CancelButtonPressed)
    # REACT to cancel button pressed
    dg.EndGrid()
    # DONE adding buttons
    # LOAD form default values
    settings=("TextBoxInputFile","TextBoxOutputFile","TextBoxJobName","TextBoxJobComment","TextBoxJobDepartment","TextBoxJobPool","TextBoxJobSecondaryPool","TextBoxJobPriority","TextBoxJobConcurrentTasks")
    dg.LoadSettings( GetSettingsFilename(), settings )
    dg.EnabledStickySaving( settings, GetSettingsFilename() )
    dg.ShowDialog(True)

def GetSettingsFilename():
    '''
    Get DEFAULT settings filename
    '''
    path=Path.Combine( RepositoryUtils.GetRootDirectory(), "custom/scripts/Submission/CrCustomFfmpegConvert.ini" )   
    # LOG path to ini file
    ClientUtils.LogText("Path ini "+path)
    return path   
def CloseDialog():
    '''
    Close current form
    '''
    global dg
    dg.CloseDialog()
def CancelButtonPressed():
    '''
    React to cancel button pressed
    '''
    CloseDialog()
def CheckErrors():
    '''
    Check for some input errors
    '''
    global dg
    return (len(dg.GetValue("TextBoxInputFile")) <=0) or (len(dg.GetValue("TextBoxOutputFile")) <=0)
def GetOutputDirectory():
    '''
    Get output directory for a job
    '''
    global dg

    pathstr=dg.GetValue("TextBoxOutputFile")
    pathlist=None
    pathdir=None
    # LOG path to job output file
    ClientUtils.LogText("Path output file "+pathstr)
    pathlist=os.path.split(pathstr)
    pathdir=pathlist[0]
    # LOG path to job output directory
    ClientUtils.LogText("Path output directory "+pathdir)
    return pathdir
def OkButtonPressed(*args):
    '''
    React to ok button pressed, make a job and run
    '''
    global dg
    # check if any errors
    global errors

    errors=False
    errors=CheckErrors()
    if errors:
        dg.ShowMessageBox( "There are input values missing", "Errors" )
        return
    # JOB info file
    # -- required to run a JOB 
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "crcustomffmpegconvert_job_info.job" )
    # open out stream
    out = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    out.WriteLine( "Plugin=CrCustomFfmpegConvert" )
    out.WriteLine( "Name=%s" % dg.GetValue( "TextBoxJobName"))
    out.WriteLine( "Comment=%s" % dg.GetValue( "TextBoxJobComment" ) )
    out.WriteLine( "Department=%s" % dg.GetValue( "TextBoxJobDepartment" ) )
    out.WriteLine( "Pool=%s" % dg.GetValue( "TextBoxJobPool" ) )
    out.WriteLine( "SecondaryPool=%s" % dg.GetValue( "TextBoxJobSecondaryPool" ) )
    out.WriteLine( "Group=%s" % dg.GetValue( "TextBoxJobGroup" ) )
    out.WriteLine( "Priority=%s" % dg.GetValue( "TextBoxJobPriority" ) )
    out.WriteLine( "ConcurrentTasks=%s" % dg.GetValue( "TextBoxJobConcurrentTasks" ) )
    out.WriteLine( "Frames=%s" % 1 )
    out.WriteLine( "ChunkSize=%s" % 1 )
    out.WriteLine(" OutputDirectory0=%s" % GetOutputDirectory())
    out.Close()
    # DONE close out stream JOB info file
    
    # PLUGIN info file
    # -- PLUGIN specific options
    # -- PLUGIN specific options read by GetPluginInfoEntry()
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "crcustomffmpegconvert_plugin_info.job" )
    # open out stream
    out = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
    out.WriteLine( "InputFile=%s" % dg.GetValue( "TextBoxInputFile"))
    out.WriteLine( "OutputFile=%s" % dg.GetValue( "TextBoxOutputFile"))
    out.Close()
    # DONE close out stream PLUGIN info file

    # Setup the command line arguments.
    arguments = StringCollection()
    
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    
    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    dg.ShowMessageBox( results, "Submission Results" )
    CloseDialog()

