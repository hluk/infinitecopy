# SPDX-License-Identifier: LGPL-2.0-or-later
from PySide6.QtCore import Property, QMimeData, QObject, QTimer, Signal, Slot
from PySide6.QtGui import QClipboard, QGuiApplication
from PySide6.QtQml import QJSValue

import infinitecopy.MimeFormats as formats


class Clipboard(QObject):
    changed = Signal(dict)

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
            self.clipboardTimer.start()
        elif mode == QClipboard.Selection:
            self.selectionTimer.start()

    def onClipboardChangedAfterDelay(self):
        self.emitChanged(QClipboard.Clipboard, formats.valueSourceClipboard)

    def onSelectionChangedAfterDelay(self):
        self.emitChanged(QClipboard.Selection, formats.valueSourceSelection)

    def emitChanged(self, mode, source):
        clipboard = QGuiApplication.clipboard()
        mimeData = clipboard.mimeData(mode)
        data = {
            format: mimeData.data(format)
            for format in self.formats
            if mimeData.hasFormat(format)
        }
        data[formats.mimeSource] = source
        self.changed.emit(data)

    @Property(str)
    def text(self):
        clipboard = QGuiApplication.clipboard()
        return clipboard.text()

    @text.setter
    def text(self, text):
        self.setData({formats.mimeText: text.encode("utf-8")})

    @Slot(QJSValue)
    def setData(self, value):
        data = value.toVariant()
        mimeData = QMimeData()
        mimeData.setData(formats.mimeOwner, b"1")
        for format_, bytes_ in data.items():
            mimeData.setData(format_, bytes_)
        clipboard = QGuiApplication.clipboard()
        clipboard.setMimeData(mimeData)
