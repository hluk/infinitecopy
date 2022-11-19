# SPDX-License-Identifier: LGPL-2.0-or-later
from PyQt6.QtCore import (
    QMimeData,
    QObject,
    QTimer,
    pyqtProperty,
    pyqtSignal,
    pyqtSlot,
)
from PyQt6.QtGui import QClipboard, QGuiApplication
from PyQt6.QtQml import QJSValue


class Clipboard(QObject):
    changed = pyqtSignal(dict)

    def __init__(self, config):
        QObject.__init__(self)
        clipboard = QGuiApplication.clipboard()
        clipboard.changed.connect(self.onClipboardChanged)

        self.clipboardTimer = QTimer()
        self.clipboardTimer.setInterval(config.clipboardChangedDelayMs)
        self.clipboardTimer.setSingleShot(True)
        self.clipboardTimer.timeout.connect(self.onClipboardChangedAfterDelay)

        self.selectionTimer = QTimer()
        self.selectionTimer.setInterval(config.selectionChangedDelayMs)
        self.selectionTimer.setSingleShot(True)
        self.selectionTimer.timeout.connect(self.onSelectionChangedAfterDelay)

        self.formats = config.formats

    def onClipboardChanged(self, mode):
        if mode == QClipboard.Clipboard:
            if not QGuiApplication.clipboard().ownsClipboard():
                self.clipboardTimer.start()
            else:
                self.clipboardTimer.stop()
        elif mode == QClipboard.Selection:
            if not QGuiApplication.clipboard().ownsSelection():
                self.selectionTimer.start()
            else:
                self.selectionTimer.stop()

    def onClipboardChangedAfterDelay(self):
        self.emitChanged(QClipboard.Clipboard)

    def onSelectionChangedAfterDelay(self):
        self.emitChanged(QClipboard.Selection)

    def emitChanged(self, mode):
        clipboard = QGuiApplication.clipboard()
        mimeData = clipboard.mimeData()
        data = {}
        for format in self.formats:
            if mimeData.hasFormat(format):
                data[format] = mimeData.data(format)
        self.changed.emit(data)

    @pyqtProperty(str)
    def text(self):
        clipboard = QGuiApplication.clipboard()
        return clipboard.text()

    @text.setter
    def text(self, text):
        clipboard = QGuiApplication.clipboard()
        return clipboard.setText(text)

    @pyqtSlot(QJSValue)
    def setData(self, value):
        data = value.toVariant()
        mimeData = QMimeData()
        for format_, bytes_ in data.items():
            mimeData.setData(format_, bytes_)
        clipboard = QGuiApplication.clipboard()
        clipboard.setMimeData(mimeData)
