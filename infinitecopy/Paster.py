# SPDX-License-Identifier: LGPL-2.0-or-later
from time import sleep

import gi
from PySide6.QtCore import (
    QCoreApplication,
    QObject,
    QTimer,
    Slot,
    qDebug,
    qWarning,
)

gi.require_version("Atspi", "2.0")
from gi.repository import Atspi  # noqa: E402

PASTE_TIMEOUT_MS = 500
TEXT_ENTRY_ROLES = [
    Atspi.Role.ENTRY,
    Atspi.Role.PASSWORD_TEXT,
]


class Paster(QObject):
    def __init__(self, view):
        super().__init__()

        self.view = view

        self.stop_timer = QTimer()
        self.stop_timer.setSingleShot(True)
        self.stop_timer.timeout.connect(Atspi.event_quit)

        self.idle_timer = QTimer()
        self.idle_timer.setInterval(1)
        self.idle_timer.timeout.connect(self._idle)

    @Slot(str)
    def paste(self, text):
        self.success = False

        def on_focus_changed(event):
            obj = event.source
            is_focused = event.detail1 == 1
            qDebug(
                f"Focus changed: {obj.get_role_name()}"
                f" {'focused' if is_focused else 'defocused'}"
            )
            if is_focused:
                if obj.role in TEXT_ENTRY_ROLES:
                    self.success = obj.insert_text(
                        obj.get_caret_offset(), text, len(text)
                    )
                    self.stop_timer.start(0)

        listener = Atspi.EventListener.new(
            self._eventWrapper, on_focus_changed
        )
        Atspi.EventListener.register(listener, "object:state-changed:focused")

        self.stop_timer.start(PASTE_TIMEOUT_MS)
        self.idle_timer.start()
        QTimer.singleShot(0, self.view.hide)
        Atspi.event_main()
        self.idle_timer.stop()

        Atspi.EventListener.deregister(
            listener, "object:state-changed:focused"
        )

        if not self.success:
            qWarning("Failed to paste text")

        return self.success

    def _idle(self):
        QCoreApplication.processEvents()
        # releases GIL
        sleep(1e-2)

    def _eventWrapper(self, event, callback):
        return callback(event)
