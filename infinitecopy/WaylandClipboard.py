# SPDX-License-Identifier: LGPL-2.0-or-later
import logging

from PySide6.QtCore import (
    Property,
    QByteArray,
    QCoreApplication,
    QElapsedTimer,
    QIODevice,
    QObject,
    QProcess,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtQml import QJSValue

import infinitecopy.MimeFormats as formats

OWN_FORMAT = "application/x-infinitcopy-owner"
PROCESS_START_TIMEOUT_MS = 5000
PROCESS_FINISH_TIMEOUT_MS = 5000

IGNORED_WL_PASTE_ERRORS = [
    "No suitable type of content copied",
    "No selection",
]

logger = logging.getLogger(__name__)


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

    logger.warning(
        "Process timeout: %s %s",
        process.program(),
        " ".join(process.arguments()),
    )

    process.terminate()
    while (
        not isFinished(process, 50)
        and elapsed.elapsed() < PROCESS_FINISH_TIMEOUT_MS
    ):
        QCoreApplication.processEvents()

    return False


def logPasteErrorOutput(process):
    err = bytes(process.readAllStandardError()).decode("utf-8").strip()
    if err not in IGNORED_WL_PASTE_ERRORS:
        logger.warning("wl-paste: %s", err)


def logCopyErrorOutput(process):
    err = bytes(process.readAllStandardError()).decode("utf-8").strip()
    logger.warning("wl-copy: %s", err)


def startWlPasteProcess(args, slot, name):
    process = QProcess()

    def changed():
        logger.debug("%s changed", name)
        process.readAllStandardOutput()
        slot()

    process.readyReadStandardOutput.connect(changed)
    process.readyReadStandardError.connect(logPasteErrorOutput)
    process.start("wl-paste", ["--watch", "echo"] + args, QIODevice.ReadOnly)
    if not process.waitForStarted(PROCESS_START_TIMEOUT_MS):
        logger.critical(
            "Failed to start clipboard monitoring with wl-paste: %s",
            process.errorString(),
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
    process = ClipboardSetterProcess(["--clear"], None)
    return process.waitForFinished()


class ClipboardDataProcess:
    def __init__(self, format_, args):
        self.process = QProcess()
        self.out = QByteArray()

        self.process.readyReadStandardOutput.connect(
            lambda: self.out.append(self.process.readAllStandardOutput())
        )
        self.process.readyReadStandardError.connect(
            lambda: logPasteErrorOutput(self.process)
        )

        self.process.start(
            "wl-paste", ["--type", format_] + args, QIODevice.ReadOnly
        )

        if not self.process.waitForStarted(PROCESS_START_TIMEOUT_MS):
            logger.critical(
                "Failed to get clipboard with wl-paste: %s",
                self.process.errorString(),
            )

    def output(self):
        waitForFinished(self.process)

        # Avoid extra new line from wl-paste output.
        if self.out.endsWith(b"\n"):
            return self.out.left(self.out.size() - 1)

        return self.out


class ClipboardSetterProcess:
    def __init__(self, args, bytes_):
        self.process = QProcess()

        self.process.readyReadStandardError.connect(
            lambda: logCopyErrorOutput(self.process)
        )
        self.process.closeReadChannel(QProcess.StandardOutput)

        self.process.start("wl-copy", args, QIODevice.ReadWrite)

        if not self.process.waitForStarted(PROCESS_START_TIMEOUT_MS):
            logger.critical(
                "Failed to set clipboard with wl-copy: %s",
                self.process.errorString(),
            )
        else:
            if bytes_:
                self.process.write(bytes_)
            self.process.closeWriteChannel()

    def waitForFinished(self):
        return waitForFinished(self.process)


class WaylandClipboard(QObject):
    changed = Signal(dict)

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

        clipboardProcess = startWlPasteProcess(
            [], self.onClipboardChanged, "clipboard"
        )
        selectionProcess = startWlPasteProcess(
            ["--primary"], self.onSelectionChanged, "selection"
        )
        self.processes = [p for p in (clipboardProcess, selectionProcess) if p]

        QCoreApplication.instance().aboutToQuit.connect(self.onAboutToQuit)

    def isOk(self):
        return self.processes and all(
            p and p.state() == QProcess.Running for p in self.processes
        )

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

    @Property(str)
    def text(self):
        data = clipboardData(formats.mimeText, [])
        return bytes(data).decode("utf-8")

    @text.setter
    def text(self, text):
        return setClipboardData(OWN_FORMAT, b"1") and setClipboardData(
            formats.mimeText, text.encode("utf-8")
        )

    @Slot(QJSValue)
    def setData(self, value):
        clearClipboardData()
        data = value.toVariant()
        processes = [
            ClipboardSetterProcess(["--type", format_], bytes_)
            for format_, bytes_ in data.items()
        ]
        for process in processes:
            process.waitForFinished()
