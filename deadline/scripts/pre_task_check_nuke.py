import os
import re
import sys
import subprocess
from System.IO import *
from Deadline.Scripting import *


def __main__(*args):
    deadlinePlugin = args[0]
    job = deadlinePlugin.GetJob()
    task = deadlinePlugin.GetCurrentTask()
    slave = deadlinePlugin.GetSlaveName()

    # check nuke availability
    deadlinePlugin.LogInfo("Checking nuke availability on this machine...")
    deadlinePluginsDir = RepositoryUtils.GetPluginsDirectory()
    nukeParamsFile = os.path.join(
        deadlinePluginsDir, "Nuke", "Nuke.param")
    nukeDeadlinePaths = FileUtils.GetIniFileSetting(
        nukeParamsFile, "RenderExecutable11_1", "Default", "C:/Program Files/Nuke11.1v3/Nuke11.1.exe;")
    nuke11path = nukeDeadlinePaths.split(";")[0]
    if not os.path.exists(nuke11path):
        deadlinePlugin.LogWarning(
            "Nuke11 is not installed on this machine! This task will fail to split denoised images. Requeuing...")
        deadlinePlugin.FailRender("Path '{}' could not be found, Nuke11 may not be installed or properly configured.".format(nuke11path))

    # check nuke licence
    deadlinePlugin.LogInfo("Checking licence for nuke...")
    slave_settings = RepositoryUtils.GetSlaveSettings(slave, True)
    slave_pools = slave_settings.SlavePools

    workstation = True if "studio_3d" in slave_pools else False

    if workstation:
        lic_file_0 = "C:/ProgramData/The Foundry/RLM/foundry_client.lic"
        lic_file_1 = "C:/ProgramData/The Foundry/RLM/foundry_client_license_crater_local_1.lic"

        if os.path.exists(lic_file_1):
            licence = 1
            licence_file = lic_file_1
        elif os.path.exists(lic_file_0):
            licence = 0
            licence_file = lic_file_0
        else:
            licence = None
            licence_file = None

        if licence == 1:
            # permanent licence installed
            deadlinePlugin.LogInfo("Licence: {}".format(licence_file))
            deadlinePlugin.LogInfo("Licence found for Nuke11!")

        if licence == 0:
            # non-permanent licence installed
            deadlinePlugin.LogInfo("Licence: {}".format(licence_file))
            available_licences = 0

            # check availability
            rlmutil = "Q:/bin/windows/rlm/rlmutil.exe"
            rlm_server_ip = "192.168.60.4"
            rlm_server_port = "4101"

            if not os.path.exists(rlmutil):
                deadlinePlugin.LogWarning(
                    "rlmutil not found in path: {}".format(rlmutil))
                deadlinePlugin.FailRender(
                    "rlmutil not found!")

            cmd = [rlmutil, "rlmstat", "-c",
                   rlm_server_port + "@" + rlm_server_ip, "-avail"]

            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            for line in proc.stdout.readlines():
                match = re.match(
                    r"(?s).*?(nuke_i)(?<=nuke_i).*?(?=available:).*?(\d{1,2}).*", line)
                if match:
                    available_licences += int(match.group(2))

            if available_licences > 0:
                deadlinePlugin.LogInfo(
                    "Available licenses for 'nuke_i': {}".format(available_licences))
                deadlinePlugin.LogInfo("Licence available for Nuke11!")
            else:
                deadlinePlugin.LogWarning(
                    "No licence available for 'nuke_i'. Requeuing...")
                deadlinePlugin.FailRender(
                    "No available licence found for Nuke11!")

        if licence == None:
            deadlinePlugin.LogInfo("Licence: {}".format(licence_file))
            deadlinePlugin.LogWarning(
                "Licence file not found. Requeuing...")
            deadlinePlugin.FailRender("No available licence found for Nuke11!")
