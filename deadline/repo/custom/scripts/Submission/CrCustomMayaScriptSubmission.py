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
    dg.SetTitle("CrCustomMayaScript")
    dg.AddGrid()
    dg.AddControlToGrid("Label1", "LabelControl", "Build", 0,0, "", False)
    dg.AddControlToGrid( "TextBoxBuild", "TextControl", "", 0, 1 )
    dg.AddControlToGrid("Label2", "LabelControl", "Version", 1,0, "", False)
    dg.AddControlToGrid( "TextBoxVersion", "TextControl", "", 1, 1 )
    dg.AddControlToGrid("Label3", "LabelControl", "Camera", 2,0, "", False)
    dg.AddControlToGrid( "TextBoxCamera", "TextControl", "", 2, 1 )
    dg.AddControlToGrid("Label4", "LabelControl", "resX", 3,0, "", False)
    dg.AddControlToGrid( "TextBoxresX", "TextControl", "", 3, 1 )
    dg.AddControlToGrid("Label5", "LabelControl", "resY", 4,0, "", False)
    dg.AddControlToGrid( "TextBoxresY", "TextControl", "", 4, 1 )
    dg.AddControlToGrid("Label55", "LabelControl", "Scene File", 5,0, "", False)
    dg.AddControlToGrid( "TextBoxSceneFile", "TextControl", "", 5, 1 )
    dg.AddControlToGrid("Label7", "LabelControl", "Scene Project", 6,0, "", False)
    dg.AddControlToGrid( "TextBoxSceneProject", "TextControl", "", 6, 1 )
    # job strings
    dg.AddControlToGrid("Label8", "LabelControl", "Job Name", 7,0, "", False)
    dg.AddControlToGrid( "TextBoxJobName", "TextControl", "", 7, 1)
    dg.AddControlToGrid("Label9", "LabelControl", "Job Comment", 8,0, "", False)
    dg.AddControlToGrid( "TextBoxJobComment", "TextControl", "", 8, 1)
    dg.AddControlToGrid("Label10", "LabelControl", "Job Department", 9,0, "", False)
    dg.AddControlToGrid( "TextBoxJobDepartment", "TextControl", "", 9, 1)
    dg.AddControlToGrid("Label11", "LabelControl", "Job Pool", 10,0, "", False)
    dg.AddControlToGrid( "TextBoxJobPool", "TextControl", "", 10, 1)
    dg.AddControlToGrid("Label12", "LabelControl", "Job Secondary Pool", 11,0, "", False)
    dg.AddControlToGrid( "TextBoxJobSecondaryPool", "TextControl", "", 11, 1)
    dg.AddControlToGrid("Label13", "LabelControl", "Job Group", 12,0, "", False)
    dg.AddControlToGrid( "TextBoxJobGroup", "TextControl", "", 12, 1)
    dg.AddControlToGrid("Label14", "LabelControl", "Job Priority", 13,0, "", False)
    dg.AddControlToGrid( "TextBoxJobPriority", "TextControl", "", 13, 1)
    dg.AddControlToGrid("Label15", "LabelControl", "Job Chunk Size (per task frames)", 14,0, "", False)
    dg.AddControlToGrid( "TextBoxJobChunkSize", "TextControl", "", 14, 1)
    dg.AddControlToGrid("Label16", "LabelControl", "Job Start Frame", 15,0, "", False)
    dg.AddControlToGrid( "TextBoxJobStartFrame", "TextControl", "", 15, 1)
    dg.AddControlToGrid("Label17", "LabelControl", "Job End Frame", 16,0, "", False)
    dg.AddControlToGrid( "TextBoxJobEndFrame", "TextControl", "", 16, 1)
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
    settings=("TextBoxBuild","TextBoxVersion","TextBoxCamera","TextBoxresX","TextBoxresY","TextBoxSceneFile","TextBoxSceneProject","TextBoxJobName","TextBoxJobComment","TextBoxJobDepartment","TextBoxJobPool","TextBoxJobSecondaryPool","TextBoxJobPriority","TextBoxJobChunkSize","TextBoxJobStartFrame","TextBoxJobEndFrame")
    dg.LoadSettings( GetSettingsFilename(), settings )
    dg.EnabledStickySaving( settings, GetSettingsFilename() )
    dg.ShowDialog(True)

def GetSettingsFilename():
    '''
    Get DEFAULT settings filename
    '''
    path=Path.Combine( RepositoryUtils.GetRootDirectory(), "custom/scripts/Submission/CrCustomMayaScript.ini" )   
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
    # or a or b or c and so on check for input optionally
    return (len(dg.GetValue("TextBoxBuild")) <=0) 
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
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "crcustommayascript_job_info.job" )
    # open out stream
    out = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    out.WriteLine( "Plugin=CrCustomMayaScript" )
    out.WriteLine( "Name=%s" % dg.GetValue( "TextBoxJobName"))
    out.WriteLine( "Comment=%s" % dg.GetValue( "TextBoxJobComment" ) )
    out.WriteLine( "Department=%s" % dg.GetValue( "TextBoxJobDepartment" ) )
    out.WriteLine( "Pool=%s" % dg.GetValue( "TextBoxJobPool" ) )
    out.WriteLine( "SecondaryPool=%s" % dg.GetValue( "TextBoxJobSecondaryPool" ) )
    out.WriteLine( "Group=%s" % dg.GetValue( "TextBoxJobGroup" ) )
    out.WriteLine( "Priority=%s" % dg.GetValue( "TextBoxJobPriority" ) )
    # COULD DO ConcurrentTasks run multiple tasks at a machine at a same time
    out.WriteLine( "ChunkSize=%s" % dg.GetValue( "TextBoxJobChunkSize" ) )
    out.WriteLine("Frames={START}-{END}".format(START=dg.GetValue("TextBoxJobStartFrame"),END=dg.GetValue("TextBoxJobEndFrame")))
    out.Close()
    # DONE close out stream JOB info file
    
    # PLUGIN info file
    # -- PLUGIN specific options
    # -- PLUGIN specific options read by GetPluginInfoEntry()
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "crcustommayascript_plugin_info.job" )
    # open out stream
    out = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
    out.WriteLine( "Build=%s" % dg.GetValue( "TextBoxBuild"))
    out.WriteLine( "Version=%s" % dg.GetValue( "TextBoxVersion"))
    out.WriteLine( "Camera=%s" % dg.GetValue( "TextBoxCamera"))
    out.WriteLine( "resX=%s" % dg.GetValue( "TextBoxresX"))
    out.WriteLine( "resY=%s" % dg.GetValue( "TextBoxresY"))
    out.WriteLine( "SceneFile=%s" % dg.GetValue( "TextBoxSceneFile"))
    out.WriteLine( "SceneProject=%s" % dg.GetValue( "TextBoxSceneProject"))
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

