# SPDX-License-Identifier: LGPL-2.0-or-later
import logging

import gi
from PySide6.QtCore import QObject, Signal

gi.require_version("Atspi", "2.0")
from gi.repository import Atspi  # noqa: E402

TEXT_ENTRY_ROLES = [
    Atspi.Role.ENTRY,
    Atspi.Role.PASSWORD_TEXT,
]

logger = logging.getLogger(__name__)


class FocusMonitor(QObject):
    text_entry_focused = Signal(object)

    def __init__(self):
        super().__init__()
        self.listener = None

    def start(self):
        logger.debug("Creating listener")
        self.listener = Atspi.EventListener.new(
            self._eventWrapper, self._on_focus_changed
        )
        logger.debug("Registering listener")
        Atspi.EventListener.register(
            self.listener, "object:state-changed:focused"
        )

        logger.debug("Starting event loop")
        Atspi.event_main()
        logger.debug("Finished event loop")

    def stop(self):
        logger.debug("Deregistering listener")
        Atspi.EventListener.deregister(
            self.listener, "object:state-changed:focused"
        )
        logger.debug("Stopping event loop")
        Atspi.event_quit()

    def _on_focus_changed(self, event):
        is_focused = event.detail1 == 1
        if is_focused and event.source.role in TEXT_ENTRY_ROLES:
            logger.debug(
                "Focus source: source: %r, role: %r",
                event.source.name,
                event.source.role,
            )
            self.text_entry_focused.emit(event.source)
        else:
            logger.debug(
                "No focus source: source: %r, focused: %r, role: %r",
                event.source.name,
                is_focused,
                event.source.role,
            )
            self.text_entry_focused.emit(None)

    def _eventWrapper(self, event, callback):
        return callback(event)
