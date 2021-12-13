import os
import sys
import logging
import webbrowser
import collections

import yaml

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

_path = os.path.dirname(__file__)
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

WINDOW_OBJECT = "cr_about"

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
WINDOW_ICON = os.path.join(os.environ["COMMON_CONFIG_ROOT"], "icons", "cr_about.png")

# -------------------------------
# Debug
# -------------------------------

from Qt import __binding__
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

    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        self.setWindowFlags(self.windowFlags() |
                            QtCore.Qt.WindowTitleHint |
                            QtCore.Qt.WindowMaximizeButtonHint |
                            QtCore.Qt.WindowMinimizeButtonHint |
                            QtCore.Qt.WindowCloseButtonHint)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Resources
        self._header = resource("header.png")

        # Set object name and window title
        self.setObjectName(WINDOW_OBJECT)
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowIcon(WINDOW_ICON)

        # Window type
        self.setWindowFlags(QtCore.Qt.Window)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        # Data
        self._data = self._get_data()
        self._indicators = self._get_indicators()

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

        header_pixmap = QtGui.QPixmap(self._header)
        header_image = QtWidgets.QLabel(self)
        header_image.setPixmap(header_pixmap)

        header.addWidget(header_image)
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(0)

        # Main
        main_layout = QtWidgets.QFormLayout()
        main_layout.setLabelAlignment(
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        for key, value in self._data.iteritems():
            label_text = str(key)
            label_tooltip_text = "Tooltip"

            label = QtWidgets.QLabel(label_text + ":")
            label.setFont(self.label_font)
            label.setToolTip(label_tooltip_text)

            info = HLabel(str(value))
            info.installEventFilter(self)
            info.setToolTip("Double click to copy to clipboard.")
            main_layout.addRow(label, info)

        main_layout.setContentsMargins(10, 2, 10, 2)
        main_layout.setSpacing(6)

        # Indicators
        indicator_layout = QtWidgets.QHBoxLayout()

        pipeui_crater_pixmap = QtGui.QPixmap(self._indicators["crater_icon_path"])
        pipeui_crater_image = QtWidgets.QLabel(self)
        pipeui_crater_image.setPixmap(pipeui_crater_pixmap)

        pipeui_shotgun_pixmap = QtGui.QPixmap(self._indicators["shotgun_icon_path"])
        pipeui_shotgun_image = QtWidgets.QLabel(self)
        pipeui_shotgun_image.setPixmap(pipeui_shotgun_pixmap)

        horizontal_spacer_indicator = QtWidgets.QSpacerItem(
            0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        
        help_button = QtWidgets.QPushButton(" ? ")

        indicator_layout.addWidget(help_button)
        indicator_layout.addItem(horizontal_spacer_indicator)
        indicator_layout.addWidget(pipeui_crater_image)
        indicator_layout.addWidget(pipeui_shotgun_image)
        indicator_layout.setContentsMargins(4, 4, 4, 4)
        indicator_layout.setSpacing(4)

        verticalSpacer = QtWidgets.QSpacerItem(
            20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        # Container
        layout = QtWidgets.QVBoxLayout(central_widget)
        layout.addLayout(header)
        layout.addWidget(QHLine())
        layout.addLayout(main_layout)
        layout.addItem(verticalSpacer)
        layout.addWidget(QHLine())
        layout.addLayout(indicator_layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Defaults
        self.setCentralWidget(central_widget)
        height = 220
        width = 400
        self.resize(width, height)
        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)

        # Signals
        help_button.clicked.connect(
            self.on_help)

    def on_help(self):
        if WINDOW_HELP:
            webbrowser.open(WINDOW_HELP)
        else:
            QtWidgets.QMessageBox.about(self, "About", "Could not get documentation URL!")

# ------------------------------

    def _get_data(self):
        data = collections.OrderedDict()

        data["Version"] = os.environ.get("PIPELINE_VERSION", "Unknown")
        data["Root"] = os.environ.get("PIPELINE_ROOT", "Unknown")
        data["Type"] = os.environ.get("PIPELINE_TYPE", "Unknown")
        
        shotgun_active = os.environ.get("SHOTGUN_PIPELINE_ACTIVE", "0")
        
        if shotgun_active == "1":
            shotgun =  "Yes"
        else:
            shotgun =  "No"

        data["Shotgun"] = shotgun

        return data

    def _get_indicators(self):
        indicators = dict()

        pipeline_type = os.environ.get("PIPELINE_TYPE", "deploy")
        shotgun_active = os.environ.get("SHOTGUN_PIPELINE_ACTIVE", "0")

        crater_icon_path = None
        shotgun_icon_path = None

        pipeui = os.path.join(os.environ["COMMON_CONFIG_ROOT"], "icons", "pipeui")

        if pipeline_type == "deploy":
            crater_icon_path = os.path.join(pipeui, "pipeui_standard_deploy.png")

            if shotgun_active == "1":
                shotgun_icon_path = os.path.join(pipeui, "pipeui_shotgun_deploy.png")
            else:
                shotgun_icon_path = os.path.join(pipeui, "pipeui_shotgun_none.png")

        elif pipeline_type == "dev":
            crater_icon_path = os.path.join(pipeui, "pipeui_standard_dev.png")

            if shotgun_active == "1":
                shotgun_icon_path = os.path.join(pipeui, "pipeui_shotgun_dev.png")
            else:
                shotgun_icon_path = os.path.join(pipeui, "pipeui_shotgun_none.png")

        else:
            print("WARNING: Could not determine pipeline type!")

        indicators["crater_icon_path"] = crater_icon_path
        indicators["shotgun_icon_path"] = shotgun_icon_path

        return indicators

# ------------------------------

    def on_exit(self):
        self.close()

# -------------------------------

    def eventFilter(self, source, event):
        if (event.type() == QtCore.QEvent.Type.MouseButtonDblClick and
                isinstance(source, QtWidgets.QLabel)):
            self.qclip.setText(source.text())
            source.setStyleSheet("QLabel {color: #82E7FE}")
            log.info("Copied to clipboard: \"%s\"", source.text())

        if (event.type() == QtCore.QEvent.Type.Enter and
                isinstance(source, QtWidgets.QLabel)):
            source.setStyleSheet("QLabel {color: white}")

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
# Application helper functions
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

def _houdini_main_window():
    """Returns Houdini's main window"""
    if hou.applicationVersion()[0] > 15:
        return hou.ui.mainQtWindow()
    else:
        return hou.qt.mainQtWindow()

def _nuke_delete_ui():
    """Delete existing UI in Nuke"""
    for obj in QtWidgets.QApplication.allWidgets():
        if obj.objectName() == WINDOW_OBJECT:
            obj.deleteLater()

def _nuke_main_window():
    """Returns Nuke's main window"""
    for obj in QtWidgets.QApplication.topLevelWidgets():
        if (obj.inherits('QMainWindow') and
                obj.metaObject().className() == 'Foundry::UI::DockMainWindow'):
            return obj
    else:
        raise RuntimeError('Could not find DockMainWindow instance')

# -------------------------------
# Entry points
# -------------------------------


def run_maya():
    """Run in Maya"""

    _maya_delete_ui()  # Delete any existing UI

    win = Window(parent=_maya_main_window())
    win.setProperty("saveWindowPref", True)

    win.show()
    module.window = win


def run_houdini():
    """Run in Houdini"""

    win = Window(parent=_houdini_main_window())
    win.setStyleSheet(hou.qt.styleSheet())
    win.setProperty("houdiniStyle", True)

    win.show()
    module.window = win

def run_nuke():
    """Run in Nuke"""

    _nuke_delete_ui()  # Delete any existing UI

    win = Window(parent=_nuke_main_window())

    win.show()
    module.window = win

# -------------------------------
# Show window
# -------------------------------

def resource(*path):
    path = os.path.join(_path, "res", *path)
    return path.replace("\\", "/")

def show():
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
        run_maya()
    elif HOUDINI:
        run_houdini()
    elif NUKE:
        run_nuke()
    else:
        log.warning("Application not supported. Exiting...")
        return
