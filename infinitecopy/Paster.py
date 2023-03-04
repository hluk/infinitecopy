# SPDX-License-Identifier: LGPL-2.0-or-later
from PySide6.QtCore import QCoreApplication, QObject, QThread, QTimer, Slot

from infinitecopy.FocusMonitor import FocusMonitor

PASTE_TIMEOUT_MS = 1000


class Paster(QObject):
    def __init__(self):
        super().__init__()
        self.focused_text_entry = None
        self.text_to_paste = None

        self.clear_timer = QTimer()
        self.clear_timer.setSingleShot(True)
        self.clear_timer.timeout.connect(self._clear_text_to_paste)

        self.monitor_thread = QThread()
        self.monitor = FocusMonitor()
        self.monitor.moveToThread(self.monitor_thread)
        self.monitor_thread.started.connect(self.monitor.start)
        self.monitor.text_entry_focused.connect(self._on_text_entry_focused)
        self.monitor_thread.start()
        QCoreApplication.instance().aboutToQuit.connect(self._stop)

    @Slot(str)
    def paste(self, text):
        self.text_to_paste = text
        if self._paste():
            return True

        self.clear_timer.start(PASTE_TIMEOUT_MS)
        return False

    def _on_text_entry_focused(self, text_entry):
        self.focused_text_entry = text_entry
        self._paste()

    def _paste(self):
        if self.text_to_paste and self.focused_text_entry:
            success = self.focused_text_entry.insert_text(
                self.focused_text_entry.get_caret_offset(),
                self.text_to_paste,
                len(self.text_to_paste),
            )
            if success:
                self.text_to_paste = None
                self.clear_timer.stop()
                return True

        return False

    def _stop(self):
        self.monitor.stop()
        self.monitor_thread.quit()
        self.monitor_thread.wait()

    def _clear_text_to_paste(self):
        self.text_to_paste = None
