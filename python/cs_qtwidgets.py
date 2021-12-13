import os
import re
import webbrowser

from Qt import QtWidgets, QtGui, QtCore


DOCS_PREFIX = "https://docs.crater.studio/doc/"
colors = {
    "prototype": "#FF8181",
    "alpha": "#FFE081",
    "beta": "#ABFF81",
    "production": "#D8D8D8",
    "other": "#D8D8D8",
}


class ReleaseBanner(QtWidgets.QWidget):
    def __init__(self, release, parent=None):
        super(ReleaseBanner, self).__init__(parent)
        self.release = release
        self.label_text = "Release: {}".format(self.release)
        self.label_text_hover = "Click for more info"

        if self.release == "Prototype":
            self.release_info = "This means it is in very early stages of developement or in " \
                "exploration phase. It should not be used in production in any circumstance " \
                "other than in very sandboxed and safe environment. If those conditions could " \
                "not be guaranteed, you are advised to stay clear from this tool."

        elif self.release == "Alpha":
            self.release_info = "This means it requires a lot of testing and consideration. " \
                "It may be used in production but with care. You are highly encouraged to use " \
                "it and report all feedback to technical department in order to make this tool " \
                "robust and production proven."

        elif self.release == "Beta":
            self.release_info = "This means the it is not quite mature enough to " \
                "be considered battle tested, but it is ready to be used extensively " \
                "in production and polished accordingly."

        elif self.release == "Production":
            self.release_info = "This means the it has been successfully used on multiple " \
                "projects. It does not mean there aren't any bugs or kwerks hanging around, " \
                "and we can always unintentionally introduce new ones, but the ideas behind " \
                "it have been properly assessed and the core of the tool has been stable for " \
                "some time now."

        else:
            self.release_info = ""

        self.setupUI()

    def setupUI(self):
        main_layout = QtWidgets.QVBoxLayout(self)

        if self.release == "Prototype":
            background_color = colors["prototype"]
        elif self.release == "Alpha":
            background_color = colors["alpha"]
        elif self.release == "Beta":
            background_color = colors["beta"]
        elif self.release == "Production":
            background_color = colors["production"]
        else:
            background_color = colors["other"]

        release_label = QtWidgets.QLabel(self.label_text)
        release_label.setAlignment(QtCore.Qt.AlignCenter)
        release_label.setObjectName("ReleaseBanner")
        release_label.installEventFilter(self)

        # needed because nuke adds shadows to labels by default
        release_label.setStyle(QtWidgets.QStyleFactory.create("Plastique"))

        # set style
        release_label.setStyleSheet(
            "#ReleaseBanner {font-family: Open Sans; color: #2b2b2b; font-size: 8pt; font-weight: bold; background-color:%s;}" % background_color)

        # layout
        main_layout.addWidget(release_label)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self._data = {
            "widget": {
                "label": release_label,
            },
        }

    def eventFilter(self, object, event):
        if event.type() == QtCore.QEvent.Enter:
            self._data["widget"]["label"].setText(self.label_text_hover)
        elif event.type() == QtCore.QEvent.Leave:
            self._data["widget"]["label"].setText(self.label_text)
        elif event.type() == QtCore.QEvent.MouseButtonPress:
            self.on_label_clicked()
        return False

    def on_label_clicked(self):
        # print("user has clicked now")
        title = "Application Release"
        message = "This is an internally developed tool. As such, it goes through " \
            "various stages: from initial proof-of-concept to production proven application.\n\n" \
            "We do not have the luxury of testing thoroughly every single script, app or procedure " \
            "before it gets into your hands. We intentionally roll them out as soon as possible and " \
            "it is the responsibility of the artists that use them to test, report and help us improve " \
            "the production toolset.\n\n"

        message += "At the moment, this application is in '{}' stage.\n\n".format(self.release)

        message += "{}".format(self.release_info)

        message_box = QtWidgets.QMessageBox(self)
        message_box.setWindowTitle(title)
        message_box.setText(message)
        message_box.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        message_box.show()


class ElidedLabel(QtWidgets.QLabel):
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        metrics = QtGui.QFontMetrics(self.font())
        elided = metrics.elidedText(self.text(), QtCore.Qt.ElideRight, self.width())
        painter.drawText(self.rect(), self.alignment(), elided)


class QHLine(QtWidgets.QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)


class QVLine(QtWidgets.QFrame):
    def __init__(self):
        super(QVLine, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.VLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)


class QHSpacer(QtWidgets.QSpacerItem):
    def __init__(self):
        super(QHSpacer, self).__init__(0, 0, QtWidgets.QSizePolicy.Expanding,
                                       QtWidgets.QSizePolicy.Minimum)


class QVSpacer(QtWidgets.QSpacerItem):
    def __init__(self):
        super(QVSpacer, self).__init__(0, 0, QtWidgets.QSizePolicy.Minimum,
                                       QtWidgets.QSizePolicy.Expanding)
