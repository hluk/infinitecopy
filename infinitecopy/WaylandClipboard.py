# SPDX-License-Identifier: LGPL-2.0-or-later
from PyQt5.QtCore import (
    QByteArray,
    QCoreApplication,
    QElapsedTimer,
    QIODevice,
    QObject,
    QProcess,
    QTimer,
    pyqtProperty,
    pyqtSignal,
    pyqtSlot,
    qCritical,
    qWarning,
)
from PyQt5.QtQml import QJSValue

import infinitecopy.MimeFormats as formats

OWN_FORMAT = "application/x-infinitcopy-owner"
PROCESS_START_TIMEOUT_MS = 5000
PROCESS_FINISH_TIMEOUT_MS = 5000

IGNORED_WL_PASTE_ERRORS = [
    "No suitable type of content copied",
    "No selection",
]


def isFinished(process, timeout):
    return process.state() == QProcess.NotRunning or process.waitForFinished(
        timeout
    )


def waitForFinished(process):
    elapsed = QElapsedTimer()
    elapsed.start()

    while (
        not isFinished(process, 50)
        and elapsed.elapsed() < PROCESS_FINISH_TIMEOUT_MS
    ):
        QCoreApplication.processEvents()

    if isFinished(process, 0):
        return True

    qWarning(
        f"Process timeout: {process.program()} {' '.join(process.arguments())}"
    )

    process.terminate()
    while (
        not isFinished(process, 50)
        and elapsed.elapsed() < PROCESS_FINISH_TIMEOUT_MS
    ):
        QCoreApplication.processEvents()

    return False


def startWlPasteProcess(args, slot):
    process = QProcess()

    def changed():
        process.readAllStandardOutput()
        slot()

    def readErrorOutput():
        err = bytes(process.readAllStandardError()).decode("utf-8").strip()
        qWarning(f"wl-paste: {err}")

    process.readyReadStandardOutput.connect(changed)
    process.readyReadStandardError.connect(readErrorOutput)
    process.start("wl-paste", ["--watch", "echo"] + args, QIODevice.ReadOnly)
    if not process.waitForStarted(PROCESS_START_TIMEOUT_MS):
        qCritical(
            "Failed to start clipboard monitoring with wl-paste: "
            f"{process.errorString()}"
        )
        return None

    return process


def ownsClipboard():
    return owns([])


def ownsSelection():
    return owns(["--primary"])


def owns(args):
    return not clipboardData(OWN_FORMAT, args).isEmpty()


def clipboardData(format_, args):
    process = ClipboardDataProcess(format_, args)
    return process.output()


def setClipboardData(format_, bytes_):
    process = ClipboardSetterProcess(["--type", format_], bytes_)
    return process.waitForFinished()


def clearClipboardData():
    process = ClipboardSetterProcess(["--clear"])
    return process.waitForFinished()


class ClipboardDataProcess:
    def __init__(self, format_, args):
        self.process = QProcess()
        self.out = QByteArray()

        self.process.readyReadStandardOutput.connect(self.readOutput)
        self.process.readyReadStandardError.connect(self.readErrorOutput)

        self.process.start(
            "wl-paste", ["--type", format_] + args, QIODevice.ReadOnly
        )

        if not self.process.waitForStarted(PROCESS_START_TIMEOUT_MS):
            qCritical(
                "Failed to get clipboard with wl-paste: "
                f"{self.process.errorString()}"
            )

    def readOutput(self):
        self.out.append(self.process.readAllStandardOutput())

    def readErrorOutput(self):
        err = (
            bytes(self.process.readAllStandardError()).decode("utf-8").strip()
        )
        if err not in IGNORED_WL_PASTE_ERRORS:
            qWarning(f"wl-paste: {err}")

    def output(self):
        waitForFinished(self.process)

        # Avoid extra new line from wl-paste output.
        if self.out.endsWith(b"\n"):
            return self.out.left(self.out.size() - 1)

        return self.out


class ClipboardSetterProcess:
    def __init__(self, args, bytes_=None):
        self.process = QProcess()

        self.process.readyReadStandardError.connect(self.readErrorOutput)
        self.process.closeReadChannel(QProcess.StandardOutput)

        self.process.start("wl-copy", args, QIODevice.ReadWrite)

        if not self.process.waitForStarted(PROCESS_START_TIMEOUT_MS):
            qCritical(
                "Failed to set clipboard with wl-copy: "
                f"{self.process.errorString()}"
            )
        else:
            if bytes_:
                self.process.write(bytes_)
            self.process.closeWriteChannel()

    def readErrorOutput(self):
        err = (
            bytes(self.process.readAllStandardError()).decode("utf-8").strip()
        )
        qWarning(f"wl-copy: {err}")

    def waitForFinished(self):
        return waitForFinished(self.process)


class WaylandClipboard(QObject):
    changed = pyqtSignal(dict)

    def __init__(self, config):
        super().__init__()

        self.clipboardTimer = QTimer()
        self.clipboardTimer.setInterval(config.clipboardChangedDelayMs)
        self.clipboardTimer.setSingleShot(True)
        self.clipboardTimer.timeout.connect(self.onClipboardChangedAfterDelay)

        self.selectionTimer = QTimer()
        self.selectionTimer.setInterval(config.selectionChangedDelayMs)
        self.selectionTimer.setSingleShot(True)
        self.selectionTimer.timeout.connect(self.onSelectionChangedAfterDelay)

        self.formats = config.formats

        clipboardProcess = startWlPasteProcess([], self.onClipboardChanged)
        selectionProcess = startWlPasteProcess(
            ["--primary"], self.onSelectionChanged
        )
        self.processes = [p for p in (clipboardProcess, selectionProcess) if p]

        QCoreApplication.instance().aboutToQuit.connect(self.onAboutToQuit)

    def onAboutToQuit(self):
        for process in self.processes:
            process.terminate()
        for process in self.processes:
            waitForFinished(process)

    def onClipboardChanged(self):
        if ownsClipboard():
            self.clipboardTimer.stop()
        else:
            self.clipboardTimer.start()

    def onSelectionChanged(self):
        if ownsSelection():
            self.selectionTimer.stop()
        else:
            self.selectionTimer.start()

    def onClipboardChangedAfterDelay(self):
        self.emitChanged([])

    def onSelectionChangedAfterDelay(self):
        self.emitChanged(["--primary"])

    def emitChanged(self, args):
        data = {}
        processes = [
            (format_, ClipboardDataProcess(format_, args))
            for format_ in self.formats
        ]

        for format_, process in processes:
            bytes_ = process.output()
            if not bytes_.isEmpty():
                data[format_] = bytes_

        if data:
            self.changed.emit(data)

    @pyqtProperty(str)
    def text(self):
        return bytes(clipboardData(formats.mimeText, [])).decode("utf-8")

    @text.setter
    def text(self, text):
        return setClipboardData(OWN_FORMAT, b"1") and setClipboardData(
            formats.mimeText, text.encode("utf-8")
        )

    @pyqtSlot(QJSValue)
    def setData(self, value):
        clearClipboardData()
        data = value.toVariant()
        processes = [
            ClipboardSetterProcess(["--type", format_], bytes_)
            for format_, bytes_ in data.items()
        ]
        for process in processes:
            process.waitForFinished()
