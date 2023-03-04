import gi
from PySide6.QtCore import QObject, Signal

gi.require_version("Atspi", "2.0")
from gi.repository import Atspi  # noqa: E402

TEXT_ENTRY_ROLES = [
    Atspi.Role.ENTRY,
    Atspi.Role.PASSWORD_TEXT,
]


class FocusMonitor(QObject):
    text_entry_focused = Signal(object)

    def __init__(self):
        super().__init__()
        self.listener = None

    def start(self):
        self.listener = Atspi.EventListener.new(
            self._eventWrapper, self._on_focus_changed
        )
        Atspi.EventListener.register(
            self.listener, "object:state-changed:focused"
        )

        Atspi.event_main()

    def stop(self):
        Atspi.EventListener.deregister(
            self.listener, "object:state-changed:focused"
        )
        Atspi.event_quit()

    def _on_focus_changed(self, event):
        is_focused = event.detail1 == 1
        if is_focused and event.source.role in TEXT_ENTRY_ROLES:
            self.text_entry_focused.emit(event.source)
        else:
            self.text_entry_focused.emit(None)

    def _eventWrapper(self, event, callback):
        return callback(event)
