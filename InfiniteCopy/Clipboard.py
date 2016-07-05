from PyQt5.QtCore import pyqtProperty, pyqtSignal, QObject, QTimer
from PyQt5.QtGui import QGuiApplication, QClipboard

class Clipboard(QObject):
    changed = pyqtSignal(str)

    def __init__(self):
        QObject.__init__(self)
        clipboard = QGuiApplication.clipboard()
        clipboard.changed.connect(self.onClipboardChanged)

        self.clipboardTimer = QTimer()
        self.clipboardTimer.setInterval(500)
        self.clipboardTimer.setSingleShot(True)
        self.clipboardTimer.timeout.connect(self.onClipboardChangedAfterDelay)

        self.selectionTimer = QTimer()
        self.selectionTimer.setInterval(1000)
        self.selectionTimer.setSingleShot(True)
        self.selectionTimer.timeout.connect(self.onSelectionChangedAfterDelay)

    def onClipboardChanged(self, mode):
        if mode == QClipboard.Clipboard:
            self.clipboardTimer.start()
        elif mode == QClipboard.Selection:
            self.selectionTimer.start()

    def onClipboardChangedAfterDelay(self):
        self.emitChanged(QClipboard.Selection)

    def onSelectionChangedAfterDelay(self):
        self.emitChanged(QClipboard.Selection)

    def emitChanged(self, mode):
        clipboard = QGuiApplication.clipboard()
        text = clipboard.text()
        self.changed.emit(text)

    @pyqtProperty(str)
    def text(self):
        clipboard = QGuiApplication.clipboard()
        return clipboard.text()

    @text.setter
    def text(self, text):
        clipboard = QGuiApplication.clipboard()
        return clipboard.setText(text)
