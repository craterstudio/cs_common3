import os
import sys
import logging
import webbrowser

import yaml

from Qt import __binding__
from Qt import QtGui
from Qt import QtCore
from Qt import QtWidgets

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

from . import version

module = sys.modules[__name__]
module.window = None

sys.dont_write_bytecode = True  # Avoid writing .pyc files
log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format='%(levelname)s: %(filename)s - %(message)s')
log.setLevel(logging.DEBUG)

# -------------------------------
# Configuration
# -------------------------------

WINDOW_OBJECT = "cr_rootpanel"

def get_tool_info():
    tool_info = dict()
    info_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "info.yml")
    if not os.path.isfile(info_file):
        return tool_info
    with open(info_file) as f:
        tool_info = yaml.load(f, Loader=yaml.FullLoader)
    return tool_info

APP_INFO = get_tool_info()
WINDOW_TITLE = APP_INFO.get("configuration", {}).get("app_name", WINDOW_OBJECT)
WINDOW_HELP = APP_INFO.get("configuration", {}).get(
    "docs_url", os.environ.get("PIPELINE_DOCS", None))
WINDOW_ICON = os.path.join(
    os.environ["COMMON_CONFIG_ROOT"], "icons", "cr_rootpanel.png")

# -------------------------------
# Debug
# -------------------------------

print('Using: ' + __binding__)

# -------------------------------
# Main class
# -------------------------------


class QHLine(QtWidgets.QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)

        if HOUDINI:
            self.setProperty("houdiniStyle", True)


class QVLine(QtWidgets.QFrame):
    def __init__(self):
        super(QVLine, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.VLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)

        if HOUDINI:
            self.setProperty("houdiniStyle", True)


class HLabel(QtWidgets.QLabel):
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)

        metrics = QtGui.QFontMetrics(self.font())
        elided = metrics.elidedText(
            self.text(), QtCore.Qt.ElideRight, self.width())

        painter.drawText(self.rect(), self.alignment(), elided)


class Window(QtWidgets.QMainWindow):

    def __init__(self, parent=None, scene_root=None):
        super(Window, self).__init__(parent)
        self.setWindowFlags(self.windowFlags() |
                            QtCore.Qt.WindowTitleHint |
                            QtCore.Qt.WindowMaximizeButtonHint |
                            QtCore.Qt.WindowMinimizeButtonHint |
                            QtCore.Qt.WindowCloseButtonHint)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Set object name and window title
        self.setObjectName(WINDOW_OBJECT)
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowIcon(QtGui.QIcon(WINDOW_ICON))

        # Window type
        self.setWindowFlags(QtCore.Qt.Window)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        # Data
        self.scene_root = scene_root
        self.scene_root_info = vars(scene_root)

        # Font
        self.label_font = QtGui.QFont()
        self.label_font.setBold(True)

        # Setup UI
        self.setupUI()
        self.qclip = QtWidgets.QApplication.clipboard()

    def setupUI(self):
        # Central widget
        central_widget = QtWidgets.QWidget()

        # Header
        header = QtWidgets.QHBoxLayout()

        version_label = QtWidgets.QLabel("v" + version)
        vertical_spacer_header = QtWidgets.QSpacerItem(
            0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        help_button = QtWidgets.QPushButton(" ? ")

        header.addWidget(version_label)
        header.addItem(vertical_spacer_header)
        header.addWidget(help_button)
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(6)

        # Scene Root Variables
        rootpanel = QtWidgets.QFormLayout()
        rootpanel.setLabelAlignment(
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        for key, value in self.scene_root_info.iteritems():
            if isinstance(value, (basestring, int)) and not key.startswith("_"):

                label_text = str(key)
                label_tooltip_text = "CRX_" + label_text.upper()

                label = QtWidgets.QLabel(label_text + ":")
                label.setFont(self.label_font)
                label.setToolTip(label_tooltip_text)
                label.setObjectName("LabelWidget_" + label_text)
                label.installEventFilter(self)
                label_tooltip_text_color = "white"

                if HOUDINI:
                    if not hou.getenv(label_tooltip_text):
                        label_tooltip_text_color = "red"
                else:
                    if label_tooltip_text not in os.environ:
                        label_tooltip_text_color = "red"

                label.setStyleSheet("""QToolTip {
                                        background-color: black;
                                        color: """ + label_tooltip_text_color + """;
                                        border: black solid 1px
                                        }""")

                info = HLabel(str(value))
                info.installEventFilter(self)
                info.setToolTip("Double click to copy to clipboard.")
                info.setObjectName("InfoWidget_" + label_text)
                rootpanel.addRow(label, info)

        rootpanel.setContentsMargins(10, 0, 10, 0)
        rootpanel.setSpacing(6)

        vertical_spacer = QtWidgets.QSpacerItem(
            20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        # Container
        layout = QtWidgets.QVBoxLayout(central_widget)
        layout.addLayout(header)
        layout.addWidget(QHLine())
        layout.addLayout(rootpanel)
        layout.addItem(vertical_spacer)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # Defaults
        self.setCentralWidget(central_widget)
        self.resize(800, rootpanel.rowCount() * 22)
        self.setMinimumSize(280, 290)
        self.setMaximumSize(1280, 640)

        # Data
        self.data = {
            "button": {
                "help": help_button,
            },
        }

        # Signals
        self.data["button"]["help"].clicked.connect(
            self.on_help)

# ------------------------------

    def on_help(self):
        if WINDOW_HELP:
            webbrowser.open(WINDOW_HELP)
        else:
            QtWidgets.QMessageBox.about(self, "About", "Could not get documentation URL!")

    def on_exit(self):
        self.close()

# -------------------------------

    def eventFilter(self, source, event):
        if (event.type() == QtCore.QEvent.Type.MouseButtonDblClick and
                isinstance(source, QtWidgets.QLabel)):

            source_text = ""
            if source.objectName().startswith("LabelWidget"):
                source_text = source.toolTip()
            else:
                source_text = source.text()

            self.qclip.setText(source_text)
            source.setStyleSheet("QLabel {color: #82E7FE}")
            log.info("Copied to clipboard: \"%s\"", source_text)

        if (event.type() == QtCore.QEvent.Type.Enter and
                isinstance(source, QtWidgets.QLabel)):
            source.setStyleSheet("QLabel {color: white}")

            if MAYA:
                # force tooltip to show even if disabled in preferences
                QtWidgets.QToolTip.showText(QtGui.QCursor().pos(), source.toolTip())

        if (event.type() == QtCore.QEvent.Type.Leave and
                isinstance(source, QtWidgets.QLabel)):
            source.setStyleSheet("")

        return super(Window, self).eventFilter(source, event)

    def showEvent(self, event):
        log.info("Starting: %s", WINDOW_TITLE)
        return super(Window, self).showEvent(event)

    def closeEvent(self, event):
        log.info("Closing: %s", WINDOW_TITLE)
        return super(Window, self).closeEvent(event)


# -------------------------------
# Application helper fucntions
# -------------------------------


def _maya_delete_ui():
    """Delete existing UI in Maya"""
    if cmds.window(WINDOW_OBJECT, q=True, exists=True):
        cmds.deleteUI(WINDOW_OBJECT)  # Delete window
    if cmds.dockControl('MayaWindow|' + WINDOW_TITLE, q=True, ex=True):
        cmds.deleteUI('MayaWindow|' + WINDOW_TITLE)  # Delete docked window


def _maya_main_window():
    """Return Maya's main window"""
    for obj in QtWidgets.QApplication.topLevelWidgets():
        if obj.objectName() == 'MayaWindow':
            return obj
    raise RuntimeError('Could not find MayaWindow instance')


def _nuke_delete_ui():
    """Delete existing UI in Nuke"""
    for obj in QtWidgets.QApplication.allWidgets():
        if obj.objectName() == WINDOW_OBJECT:
            obj.deleteLater()


def _nuke_set_zero_margins(widget_object):
    """Remove Nuke margins when docked UI
    .. _More info:
        https://gist.github.com/maty974/4739917
    """
    parentApp = QtWidgets.QApplication.allWidgets()
    parentWidgetList = []
    for parent in parentApp:
        for child in parent.children():
            if widget_object.__class__.__name__ == child.__class__.__name__:
                parentWidgetList.append(parent.parentWidget())
                try:
                    twoup = parent.parentWidget().parentWidget()
                    parentWidgetList.append(twoup)
                    threeup = twoup.parentWidget()
                    parentWidgetList.append(threeup)
                except AttributeError:
                    pass

                for sub in parentWidgetList:
                    if sub is not None:
                        for tinychild in sub.children():
                            try:
                                tinychild.setContentsMargins(0, 0, 0, 0)
                            except AttributeError:
                                pass


def _nuke_main_window():
    """Returns Nuke's main window"""
    for obj in QtWidgets.QApplication.instance().topLevelWidgets():
        if (
            obj.inherits("QMainWindow")
            and obj.metaObject().className() == "Foundry::UI::DockMainWindow"
        ):
            return obj
    else:
        raise RuntimeError("Could not find DockMainWindow instance")
    

def _houdini_main_window():
    """Returns Houdini's main window"""
    return hou.ui.mainQtWindow()


# -------------------------------
# Entry points
# -------------------------------


def run_maya(scene_root):
    """Run in Maya"""

    _maya_delete_ui()  # Delete any existing UI

    win = Window(parent=_maya_main_window(), scene_root=scene_root)
    win.setProperty("saveWindowPref", True)

    win.show()
    module.window = win


def run_nuke(scene_root):
    """Run in Nuke"""

    _nuke_delete_ui()  # Delete any alrady existing UI

    win = Window(parent=_nuke_main_window(), scene_root=scene_root)
    win.setWindowFlags(QtCore.Qt.Tool)

    win.show()
    module.window = win


def run_houdini(scene_root):
    """Run in houdini"""

    if scene_root.fullname == "untitled.hip":
        log.warning("Scene not saved. Cannot run application. Exiting...")
        return

    win = Window(parent=_houdini_main_window(), scene_root=scene_root)
    win.setStyleSheet(hou.qt.styleSheet())
    win.setProperty("houdiniStyle", True)

    win.show()
    module.window = win


# -------------------------------
# Show window
# -------------------------------


def show():
    if "scene_root" not in globals():
        try:
            from legacy_pipeline import pipeline_tools
            reload(pipeline_tools)
            scene_root = pipeline_tools.Scene_root()
        except Exception as err:
            log.warning(err.message)
            return

    if scene_root.path:
        scene_path_split = scene_root.path.split("/")
        if len(scene_path_split) < 7:
            log.warning(
                "Scene does not appear to be saved under standard folder structure. Exiting...")
            return
    else:
        log.warning(
            "Scene does not appear to be saved under standard folder structure. Exiting...")
        return

    if module.window is not None:
        try:
            module.window.show()

            # If the window is minimized then un-minimize it.
            if module.window.windowState() & QtCore.Qt.WindowMinimized:
                module.window.setWindowState(QtCore.Qt.WindowActive)

            # Raise and activate the window
            module.window.raise_()             # for MacOS
            module.window.activateWindow()     # for Windows
            return
        except RuntimeError as e:
            if not e.message.rstrip().endswith("already deleted."):
                raise

            # Garbage collected
            module.window = None

    if MAYA:
        run_maya(scene_root)
    elif HOUDINI:
        run_houdini(scene_root)
    elif NUKE:
        run_nuke(scene_root)
    else:
        log.warning("Application not supported. Exiting...")
        return
