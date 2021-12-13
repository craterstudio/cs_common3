import os
import traceback
import sgtk
from sgtk.platform.qt import QtCore, QtGui


logger = sgtk.platform.get_logger(__name__)


def check_current_context(context):
    if not hasattr(context, "task"):
        return False

    task = context.task
    if not task:
        return False

    return True


def initialize_context(current_file):
    engine = sgtk.platform.current_engine()
    engine_name = engine.name

    # init text
    message = ""

    # initialize tk and context from path
    tk = sgtk.sgtk_from_path(current_file)
    ctx = tk.context_from_path(current_file)

    if not tk:
        message += "-- [ERROR] Could not initialize sgtk module!\n"

    if not ctx:
        message += "-- [ERROR] Could not initialize context from current file!\n"

    # now, find a template that matches this path.  If
    # we find one and it contains the "filetag" key then we
    # can use that to try to find a Task and refine
    # the context:
    try:
        template = tk.template_from_path(current_file)
        if template and "task_name" in template.keys:
            fields = template.get_fields(current_file)
            task_name = fields.get("task_name")
            step_short_code = fields.get("Step")

            if task_name and step_short_code:
                message += "-- Task found..\n"
                # use the file tag to look up the task from Shotgun
                # for this entity:
                step_name = tk.shotgun.find("Step", [["short_name", "is", step_short_code]], ["code"])[0]["code"]
                filters = [["step", "name_is", step_name], ["content", "is", task_name], ["entity", "is", ctx.entity]]
                sg_results = tk.shotgun.find("Task", filters)

                if sg_results:
                    message += "-- Context fields found..\n"
                    # awesome, found a task so lets create a new
                    # context from it:
                    sg_result = sg_results[0]

                    ctx = tk.context_from_entity(sg_result["type"], sg_result["id"])
        message += "-- Context found..\n"
    except Exception as e:
        # failed to find a task so lets just go with the non-task context
        logger.error(e)
        message += "-- [ERROR] Could not find proper context!\n"

    try:
        # now destroy engine
        logger.info("Destroying engine..")
        if engine:
            logger.info("Destroying engine..")
            engine.destroy()

        # and start it with new context
        logger.info("Starting engine with new context..")
        if not engine_name:
            raise Exception("Application not supported.")
        else:
            sgtk.platform.start_engine(engine_name, tk, ctx)

            message += "-- Context initialized..\n"
            message += "\n"
            message += "Everythin went smoothly.\n"
            message += "Please use Shotgun menu in the future!\n"
    except Exception as e:
        # failed to find a task so lets just go with the non-task context
        logger.error(e)
        message = "-- [ERROR] Coult not initialize context.\n"
        message += "\n"
        message = "Please close maya and open it again via Shotgun Desktop, and use \"File Open\" from Shotgun menu.\n"

    return message


def main(context):

    engine = sgtk.platform.current_engine()
    if not engine:
        return

    engine_name = engine.name

    if engine_name == "tk-maya":
        import maya.cmds as cmds
        current_file = cmds.file(query=True, sceneName=True)
    elif engine_name == "tk-nuke":
        import nuke
        current_file = nuke.root().name()
    elif engine_name == "tk-houdini":
        import hou
        current_file = hou.hipFile.path()
    else:
        raise Exception("Current application is not supported.")

    if not os.path.isfile(current_file):
        logger.info("File not found or is not saved, skipping this step...")
    else:
        check = check_current_context(context)

        if check:
            logger.info("Context fully initialized...")
        else:
            title = "Shotgun Context Warning"

            message = ""
            message += "There seems to be a problem."
            message += "\n\n"
            message += "Looks like you opened a scene by traditional methods rather than via "
            message += "Shotgun \"File Open\" dialog."
            message += "\n\n"
            message += "Do you want to try and establish proper context for this file automatically?"

            confirm_dialog = QtGui.QMessageBox.warning(
                None, title, message, QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)

            if confirm_dialog == QtGui.QMessageBox.Yes:
                return_msg = initialize_context(current_file)

                # print message to user
                QtGui.QMessageBox.information(
                    None, "Shotgun Context", return_msg, QtGui.QMessageBox.Ok)
