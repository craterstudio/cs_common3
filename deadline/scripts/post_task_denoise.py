import re
import os
import subprocess
from System.IO import *
from Deadline.Scripting import *


def __main__(*args):
    deadlinePlugin = args[0]
    job = deadlinePlugin.GetJob()
    outputDirectories = job.OutputDirectories
    outputFilenames = job.OutputFileNames
    paddingRegex = re.compile("[^\\?#]*([\\?#]+).*")

    get_denoise_AOVs = job.GetJobExtraInfoKeyValue("denoise_AOVs")
    denoise_AOVs = [x.strip() for x in get_denoise_AOVs.split(',')]

    get_denoise_parameters = job.GetJobExtraInfoKeyValue("denoise_parameters")
    denoise_parameters = [x.strip() for x in get_denoise_parameters.split(',')]

    get_utility_bitdepth = job.GetJobExtraInfoKeyValue("utility_bitdepth")
    utility_bitdepth = int(get_utility_bitdepth)

    get_utility_passes = job.GetJobExtraInfoKeyValue("utility_passes")
    utility_passes = [x.strip() for x in get_utility_passes.split(',')]

    get_denoise_split_layers = job.GetJobExtraInfoKeyValue("denoise_split_layers")
    denoise_split_layers = bool(get_denoise_split_layers)

    get_aovs_merged = job.GetJobExtraInfoKeyValue("aovs_merged")
    aovs_merged = bool(get_aovs_merged)

    for i in range(0, len(outputDirectories)):
        outputDirectory = outputDirectories[i]
        outputFilename = outputFilenames[i]

        startFrame = deadlinePlugin.GetStartFrame()
        endFrame = deadlinePlugin.GetEndFrame()
        for frameNum in range(startFrame, endFrame + 1):

            taskFile = Path.Combine(outputDirectory, outputFilename)
            taskFile = taskFile.replace("//", "/")

            m = re.match(paddingRegex, taskFile)
            if(m != None):
                padding = m.group(1)
                frame = StringUtils.ToZeroPaddedString(
                    frameNum, len(padding), False)
                taskFile = taskFile.replace(padding, frame)

            # get necesery information
            deadlineCustomPluginsDir = RepositoryUtils.GetCustomPluginsDirectory()
            noiceParamsFile = os.path.join(
                deadlineCustomPluginsDir, "Noice", "Noice.param")
            noiceDeadlinePaths = FileUtils.GetIniFileSetting(
                noiceParamsFile, "Noice_RenderExecutable_5_2_2_1", "Default", "Q:/resources/maya/plugins/mtoadeploy/2018_3.1.2.1/bin/noice.exe;")
            noicePath = noiceDeadlinePaths.split(";")[0]

            # fail render if noice.ex not found
            if not os.path.isfile(noicePath):
                deadlinePlugin.FailRender("Noice executable could not be found at: {}".format(noicePath))

            outputDirectoryName = os.path.basename(os.path.normpath(outputDirectory))
            denoiseDirectory = os.path.join(os.path.abspath(os.path.join(outputDirectory, os.pardir)), outputDirectoryName + "_denoised")
            newFilePath = os.path.join(denoiseDirectory, outputFilename).replace(padding, frame)

            # create denoise folder if it doesnt exist
            if not os.path.exists(denoiseDirectory):
                os.makedirs(denoiseDirectory)

            # create denoise command
            extraAOVs = ""
            if denoise_AOVs[0] != "":
                for item in denoise_AOVs:
                    extraAOVs = extraAOVs + " -l " + item

            patch_radius = denoise_parameters[0]
            search_radius = denoise_parameters[1]
            variance = denoise_parameters[2]

            noiceCmd = "\"" + noicePath + "\" -i \"" + taskFile + "\"" + extraAOVs + " -pr " + \
                patch_radius + " -sr " + search_radius + " -v " + \
                variance + " -o \"" + newFilePath + "\""

            # log task information
            deadlinePlugin.LogInfo("Noice Path:     " + noicePath)
            deadlinePlugin.LogInfo("Extra AOVs:     " + str(denoise_AOVs))
            deadlinePlugin.LogInfo("Patch Radius:   " + patch_radius)
            deadlinePlugin.LogInfo("Search Radius:  " + search_radius)
            deadlinePlugin.LogInfo("Variance:       " + variance)
            deadlinePlugin.LogInfo("Noice Command:  " + "[" + noiceCmd + "]")
            deadlinePlugin.LogInfo("Denoising File: " + taskFile)
            deadlinePlugin.LogInfo("New File:       " + newFilePath)

            # denoise command execute
            p = subprocess.Popen(noiceCmd, stdout=subprocess.PIPE, shell=True)
            (output, err) = p.communicate()

            p_status = p.wait()
            print(output)
            print("Exit Code: {}".format(str(p_status)))

            # fail render if error code 1
            if p_status == 1:
                deadlinePlugin.FailRender("Denoising failed.")

            #
            # SPLIT LAYERS
            #
            deadlinePlugin.LogInfo("Splitting denoised images...")

            deadlinePluginsDir = RepositoryUtils.GetPluginsDirectory()
            nukeParamsFile = os.path.join(
                deadlinePluginsDir, "Nuke", "Nuke.param")
            nukeDeadlinePaths = FileUtils.GetIniFileSetting(
                nukeParamsFile, "RenderExecutable11_1", "Default", "C:/Program Files/Nuke11.1v3/Nuke11.1.exe;")

            nuke10path = nukeDeadlinePaths.split(";")[0]

            if not os.path.exists(nuke10path):
                deadlinePlugin.LogWarning(
                    "Nuke 10 is not installed on this machine! This task will fail to split denoised images. Requeuing...")
                deadlinePlugin.FailRender("Nuke 10 is not installed!")

            network_repo_config_root = os.environ["NETWORK_REPO_CONFIG_ROOT"]
            render_single_exrs = os.path.join(
                network_repo_config_root, "cs_common", "deadline", "scripts", "post_task_denoise_render_exrs.py")

            if not os.path.exists(render_single_exrs):
                deadlinePlugin.LogWarning(
                    "Depended python file not found! This task will fail to split denoised images. Requeuing...")
                deadlinePlugin.FailRender("Depended python file not found!")

            # create nuke command for creating nuke script
            input_file = taskFile.replace("\\", "/")
            output_file = newFilePath.replace("\\", "/")

            nuke_cmd = "\"" + nuke10path + "\" -t \"" + render_single_exrs + \
                "\" \"" + input_file + "\" \"" + output_file + \
                "\" \"" + get_utility_bitdepth + "\" \"" + \
                get_utility_passes + "\" \"" + get_denoise_split_layers + "\""

            # log spliting info
            deadlinePlugin.LogInfo("Nuke Path:      " + nuke10path)
            deadlinePlugin.LogInfo("Nuke Script:    " + render_single_exrs)
            deadlinePlugin.LogInfo("Nuke Command:   " + "[" + nuke_cmd + "]")

            # nuke command execute
            p = subprocess.Popen(nuke_cmd, stdout=subprocess.PIPE, shell=True)
            (output, err) = p.communicate()

            p_status = p.wait()
            print(output)
            print("Exit Code: {}".format(str(p_status)))

            # fail render if error code 1
            if p_status == 1:
                deadlinePlugin.FailRender("Splitting failed.")

            deadlinePlugin.LogInfo("Post task procedure finished!")
