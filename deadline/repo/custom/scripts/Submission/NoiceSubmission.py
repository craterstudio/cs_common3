import os

from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *

from Deadline.Scripting import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

########################################################################
## Globals
########################################################################
scriptDialog = None
settings = None
errors = ""
warnings = ""

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global settings
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit Arnold Noice Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'Noice' ) )

    scriptDialog.AddTabControl("Tabs", 0, 0)

    scriptDialog.AddTabPage("Job Options")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator1", "SeparatorControl", "Job Description", 0, 0, colSpan=2 )

    scriptDialog.AddControlToGrid( "NameLabel", "LabelControl", "Job Name", 1, 0, "The name of your job. This is optional, and if left blank, it will default to 'Untitled'.", False )
    scriptDialog.AddControlToGrid( "NameBox", "TextControl", "Untitled", 1, 1 )

    scriptDialog.AddControlToGrid( "CommentLabel", "LabelControl", "Comment", 2, 0, "A simple description of your job. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "CommentBox", "TextControl", "", 2, 1 )

    scriptDialog.AddControlToGrid( "DepartmentLabel", "LabelControl", "Department", 3, 0, "The department you belong to. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "DepartmentBox", "TextControl", "", 3, 1 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator2", "SeparatorControl", "Job Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "PoolLabel", "LabelControl", "Pool", 1, 0, "The pool that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "PoolBox", "PoolComboControl", "none", 1, 1 )

    scriptDialog.AddControlToGrid( "SecondaryPoolLabel", "LabelControl", "Secondary Pool", 2, 0, "The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Slaves.", False )
    scriptDialog.AddControlToGrid( "SecondaryPoolBox", "SecondaryPoolComboControl", "", 2, 1 )

    scriptDialog.AddControlToGrid( "GroupLabel", "LabelControl", "Group", 3, 0, "The group that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "GroupBox", "GroupComboControl", "none", 3, 1 )

    scriptDialog.AddControlToGrid( "PriorityLabel", "LabelControl", "Priority", 4, 0, "A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority and 100 is the highest priority.", False )
    scriptDialog.AddRangeControlToGrid( "PriorityBox", "RangeControl", RepositoryUtils.GetMaximumPriority() / 2, 0, RepositoryUtils.GetMaximumPriority(), 0, 1, 4, 1 )

    scriptDialog.AddControlToGrid( "TaskTimeoutLabel", "LabelControl", "Task Timeout", 5, 0, "The number of minutes a slave has to render a task for this job before it requeues it. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "TaskTimeoutBox", "RangeControl", 0, 0, 1000000, 0, 1, 5, 1 )
    scriptDialog.AddSelectionControlToGrid( "AutoTimeoutBox", "CheckBoxControl", False, "Enable Auto Task Timeout", 5, 2, "If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job. " )

    scriptDialog.AddControlToGrid( "ConcurrentTasksLabel", "LabelControl", "Concurrent Tasks", 6, 0, "The number of tasks that can render concurrently on a single slave. This is useful if the rendering application only uses one thread to render and your slaves have multiple CPUs.", False )
    scriptDialog.AddRangeControlToGrid( "ConcurrentTasksBox", "RangeControl", 1, 1, 16, 0, 1, 6, 1 )
    scriptDialog.AddSelectionControlToGrid( "LimitConcurrentTasksBox", "CheckBoxControl", True, "Limit Tasks To Slave's Task Limit", 6, 2, "If you limit the tasks to a slave's task limit, then by default, the slave won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual slaves by an administrator." )

    scriptDialog.AddControlToGrid( "MachineLimitLabel", "LabelControl", "Machine Limit", 7, 0, "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "MachineLimitBox", "RangeControl", 0, 0, 1000000, 0, 1, 7, 1 )
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 7, 2, "You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist." )

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 8, 0, "The whitelisted or blacklisted list of machines.", False )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 8, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 9, 0, "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 9, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 10, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 10, 1, colSpan=2 )
    
    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 11, 0, "If desired, you can automatically archive or delete the job when it completes.", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 11, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 11, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render." )
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()

    scriptDialog.AddTabPage("Noice Options")
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Noice Options", 0, 0, colSpan=4 )
    
    scriptDialog.AddControlToGrid( "InputLabel", "LabelControl", "Input Image(s)", 1, 0, "Specify the input .vrimg or .exr file; can contain wildcards, f.e. \"c:\\path\\to\\files\\sequence_????.exr\" to denoise a sequence of frames.", False )
    scriptDialog.AddSelectionControlToGrid( "InputBox", "FileBrowserControl", "", "OpenEXR (*.exr);;All Files (*)", 1, 1, colSpan=3 )

    useFramesCheck = scriptDialog.AddSelectionControlToGrid( "UseFramesCheck", "CheckBoxControl", False, "Render Frame Range ", 2, 0, "If enabled, will only render the frames specified in the frame list field.", colSpan=2 )
    useFramesCheck.ValueModified.connect( UseFrameListModified )

    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 3, 0, "The list of frames to render.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 3, 1 )

    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 3, 2, "This is the number of frames that will be rendered at a time for each job task.", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1, 0, 1, 3, 3 )
    
    scriptDialog.AddSelectionControlToGrid( "SkipExistingCheck", "CheckBoxControl", False, "Skip Existing Images ", 5, 0, "Skip an input image if the corresponding output image already exists.", colSpan=2 )
    scriptDialog.AddSelectionControlToGrid( "ElementsCheck", "CheckBoxControl", False, "Denoise Render Elements", 5, 2, "If False, the colors in the final image are denoised in one pass;\nwhen True, the render elements are denoised separately and\nthen composited together.\n(default is False - single pass RGB denoising only)", colSpan=2 )
    
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Advanced Options", 7, 0, colSpan=4 )
    
    overridePatchRadiusCheck = scriptDialog.AddSelectionControlToGrid( "OverridePatchRadiusCheck", "CheckBoxControl", False, "Override Patch Radius", 8, 0, "", colSpan=2 )
    overridePatchRadiusCheck.ValueModified.connect( OverridePatchRadiusModified )
    
    scriptDialog.AddControlToGrid( "PatchRadiusLabel", "LabelControl", "Patch Radius", 8, 2, "", False )
    scriptDialog.AddRangeControlToGrid( "PatchRadiusBox", "RangeControl", 3, 1, 9, 0, 1, 8, 3 )
    
    overrideSearchRadiusCheck = scriptDialog.AddSelectionControlToGrid( "OverrideSearchRadiusCheck", "CheckBoxControl", False, "Override Search Radius", 9, 0, "Override the Search Radius.", colSpan=2 )
    overrideSearchRadiusCheck.ValueModified.connect( OverrideSearchRadiusModified )
    
    scriptDialog.AddControlToGrid( "SearchRadiusLabel", "LabelControl", "Search Radius", 9, 2, "", False )
    scriptDialog.AddRangeControlToGrid( "SearchRadiusBox", "RangeControl", 9, 1, 30, 0, 1, 9, 3 )
    
    overrideVarianceCheck = scriptDialog.AddSelectionControlToGrid( "OverrideVarianceCheck", "CheckBoxControl", False, "Override Variance", 10, 0, "Override the Pixel Variance.", colSpan=2 )
    overrideVarianceCheck.ValueModified.connect( OverrideVarianceModified )
    
    scriptDialog.AddControlToGrid( "VarianceLabel", "LabelControl", "Pixel Variance", 10, 2, "Specifies pixel Variance for denoising. Larger values slow down the denoiser, but may produce smoother results.", False )
    scriptDialog.AddRangeControlToGrid( "VarianceBox", "RangeControl", 0.5, 0.1, 1, 1, 0.1, 10, 3 )
    
    scriptDialog.AddControlToGrid( "AdditionalFramesLabel", "LabelControl", "Number of Additional Frames", 12,0, "Force image split in N Additional Frames. (default is 0 - use split count heuristic)", False )
    scriptDialog.AddRangeControlToGrid("AdditionalFramesBox", "RangeControl", 0, 0, 2, 0, 1, 12, 1)

    scriptDialog.AddControlToGrid("AdditionalAOVsLabel", "LabelControl", "Additional AOVs", 13, 0, "", False)
    scriptDialog.AddSelectionControlToGrid("AdditionalAOVsBox", "TextControl", "", "", 13, 1, colSpan=3)

    scriptDialog.AddControlToGrid("Separator4", "SeparatorControl", "Output", 14, 0, colSpan=4)

    scriptDialog.AddControlToGrid("OutputLabel", "LabelControl", "Output Folder", 15, 0, "", False)
    scriptDialog.AddSelectionControlToGrid("OutputBox", "FolderBrowserControl", "", "", 15, 1, colSpan=3)

    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()

    scriptDialog.EndTabControl()

    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 23, 0 )

    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 23, 3, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)

    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 23, 4, expand=False )
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    scriptDialog.EndGrid()

    settings = ("DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","FramesBox","ChunkSizeBox","ThreadsBox","SubmitSceneBox","InputBox","OutputBox","SkipExistingCheck","ElementsCheck","PatchRadiusBox","SearchRadiusBox","VarianceBox","AdditionalFramesBox" )
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    OverridePatchRadiusModified( None )
    OverrideSearchRadiusModified( None )
    OverrideVarianceModified( None )
    UseFrameListModified( None )
    
    scriptDialog.ShowDialog( False )
        
def GetSettingsFilename():
    return Path.Combine( ClientUtils.GetUsersSettingsDirectory(), "NoiceSettings.ini" )   

def OverridePatchRadiusModified( *args ):
    global scriptDialog
    enabled = scriptDialog.GetValue( "OverridePatchRadiusCheck" )
    
    scriptDialog.SetEnabled( "PatchRadiusLabel", enabled )
    scriptDialog.SetEnabled("PatchRadiusBox", enabled)
    
def OverrideSearchRadiusModified( *args ):
    global scriptDialog
    enabled = scriptDialog.GetValue( "OverrideSearchRadiusCheck" )
    
    scriptDialog.SetEnabled( "SearchRadiusLabel", enabled )
    scriptDialog.SetEnabled( "SearchRadiusBox", enabled )
    

def OverrideVarianceModified(*args):
    global scriptDialog
    enabled = scriptDialog.GetValue( "OverrideVarianceCheck" )
    
    scriptDialog.SetEnabled( "VarianceLabel", enabled )
    scriptDialog.SetEnabled( "VarianceBox", enabled )    

def UseFrameListModified( *args ):
    global scriptDialog
    enabled = scriptDialog.GetValue( "UseFramesCheck" )

    scriptDialog.SetEnabled( "FramesBox", enabled )
    scriptDialog.SetEnabled( "FramesLabel", enabled )
    scriptDialog.SetEnabled( "ChunkSizeBox", enabled )
    scriptDialog.SetEnabled( "ChunkSizeLabel", enabled )

def SubmitButtonPressed( *args ):
    global scriptDialog
    global errors
    global warnings

    warnings = ""
    errors = ""
    inputPath = scriptDialog.GetValue("InputBox")
    outputPath = scriptDialog.GetValue("OutputBox")

    skipExisting = scriptDialog.GetValue("SkipExistingCheck")

    if inputPath == "":
        errors += "No input path selected.\n"
    elif PathUtils.IsPathLocal( inputPath ):
        warnings += "The selected input path " + inputPath + " is local.\n"
    
    if bool( scriptDialog.GetValue( "UseFramesCheck" ) ):
        frames = scriptDialog.GetValue( "FramesBox" )
        if( not FrameUtils.FrameRangeValid( frames ) ):
            errors += "Frame range %s is not valid.\n\n" % frames

    if len( errors ) > 0:
        errors = "The following errors were encountered:\n%s\nPlease resolve these issues and submit again.\n" % errors
        scriptDialog.ShowMessageBox( errors, "Errors" )
        return
    else:
        if len( warnings ) > 0:
            result = scriptDialog.ShowMessageBox( "Warnings:\n%s\nDo you still want to continue?" % warnings, "Warnings", ( "Yes","No" ) )
            if result == "No":
                return

        # Create job info file.
        jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "noice_job_info.job" )
        writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
        writer.WriteLine( "Plugin=Noice" )
        writer.WriteLine( "Name=%s" % scriptDialog.GetValue( "NameBox" ) )
        writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
        writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
        writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
        writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
        writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
        writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "PriorityBox" ) )
        writer.WriteLine( "TaskTimeoutMinutes=%s" % scriptDialog.GetValue( "TaskTimeoutBox" ) )
        writer.WriteLine( "EnableAutoTimeout=%s" % scriptDialog.GetValue( "AutoTimeoutBox" ) )
        writer.WriteLine( "ConcurrentTasks=%s" % scriptDialog.GetValue( "ConcurrentTasksBox" ) )
        writer.WriteLine( "LimitConcurrentTasksToNumberOfCpus=%s" % scriptDialog.GetValue( "LimitConcurrentTasksBox" ) )
        
        writer.WriteLine( "MachineLimit=%s" % scriptDialog.GetValue( "MachineLimitBox" ) )
        if( bool(scriptDialog.GetValue( "IsBlacklistBox" ) ) ):
            writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
        else:
            writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
        
        writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )
        writer.WriteLine( "JobDependencies=%s" % scriptDialog.GetValue( "DependencyBox" ) )
        writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )
        
        if( bool( scriptDialog.GetValue( "SubmitSuspendedBox" ) ) ):
            writer.WriteLine( "InitialStatus=Suspended" )

        if bool( scriptDialog.GetValue( "UseFramesCheck" ) ):
            frames = scriptDialog.GetValue( "FramesBox" )
            chunkSize = scriptDialog.GetValue( "ChunkSizeBox" )
        else:
            frames = 1
            chunkSize = 1

        writer.WriteLine( "Frames=%s" % frames )
        writer.WriteLine( "ChunkSize=%s" % chunkSize )
        
        writer.WriteLine(" OutputDirectory0=%s" % outputPath )

        writer.Close()

        # Create plugin info file.
        pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "noice_plugin_info.job" )
        writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )

        writer.WriteLine( "Version=%s" % 5 )
        writer.WriteLine( "InputFile=%s" % inputPath )
        writer.WriteLine( "OutputFolder=%s" % outputPath )
        writer.WriteLine( "PatchRadius=%s" % scriptDialog.GetValue("PatchRadiusBox" ) )
        writer.WriteLine( "SearchRadius=%s" % scriptDialog.GetValue("SearchRadiusBox" ) )
        writer.WriteLine( "Variance=%s" % scriptDialog.GetValue("VarianceBox" ) )
        writer.WriteLine( "AdditionalFrames=%s" % scriptDialog.GetValue("AdditionalFramesBox" ) )
        writer.WriteLine( "AdditionalAOVs=%s" % scriptDialog.GetValue("AdditionalAOVsBox" ) )
        writer.WriteLine( "UsingFrames=%s" % scriptDialog.GetValue( "UseFramesCheck" ) )
        writer.WriteLine( "SkipExisting=%s" % skipExisting )

        writer.Close()
    
    # Setup the command line arguments.
    arguments = StringCollection()
    
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    
    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )
