# SPDX-License-Identifier: LGPL-2.0-or-later
import logging
from dataclasses import dataclass

import gi
from PySide6.QtCore import QObject, Signal

gi.require_version("Atspi", "2.0")
from gi.repository import Atspi  # noqa: E402

TEXT_ENTRY_ROLES = [
    Atspi.Role.ENTRY,
    Atspi.Role.PASSWORD_TEXT,
]


def flags(*flags):
    return sum(1 << f for f in flags)


MOD_MASKS = [
    Atspi.ModifierType.ALT,
    Atspi.ModifierType.CONTROL,
    Atspi.ModifierType.META,
    Atspi.ModifierType.META2,
    Atspi.ModifierType.META3,
    Atspi.ModifierType.SHIFT,
    flags(Atspi.ModifierType.ALT, Atspi.ModifierType.CONTROL),
    flags(Atspi.ModifierType.ALT, Atspi.ModifierType.META),
    flags(Atspi.ModifierType.ALT, Atspi.ModifierType.SHIFT),
    flags(Atspi.ModifierType.CONTROL, Atspi.ModifierType.META),
    flags(Atspi.ModifierType.CONTROL, Atspi.ModifierType.SHIFT),
    flags(Atspi.ModifierType.SHIFT, Atspi.ModifierType.META),
]

logger = logging.getLogger(__name__)


def modifier_list(m):
    return [modmask.value_nick for modmask in MOD_MASKS if m & (1 << modmask)]


@dataclass
class KeyEvent:
    keycode: int
    pressed: bool
    modifiers: list[str]
    text: str
    is_text: bool
    consumed: bool = False


class FocusMonitor(QObject):
    text_entry_focused = Signal(object)
    key_event = Signal(KeyEvent)

    def __init__(self):
        super().__init__()
        self.listener = None
        self.key_listener = None

    def start(self):
        logger.debug("Registering listeners")

        self.listener = Atspi.EventListener.new(
            self._eventWrapper, self._on_focus_changed
        )
        logger.debug("Registering listener")
        Atspi.EventListener.register(
            self.listener, "object:state-changed:focused"
        )

        self.key_listener = Atspi.DeviceListener.new(
            self._eventWrapper, self._on_key_press
        )
        for modmask in MOD_MASKS:
            Atspi.register_keystroke_listener(
                self.key_listener,
                key_set=None,
                modmask=modmask,
                event_types=flags(
                    Atspi.KeyEventType.PRESSED,
                    Atspi.KeyEventType.RELEASED,
                ),
                sync_type=(
                    # Consume the event and do not pass to the target app
                    # if the event handler returns True.
                    Atspi.KeyListenerSyncType.CANCONSUME
                    # Process the event before the target app.
                    | Atspi.KeyListenerSyncType.SYNCHRONOUS
                    # This might work better in some environments:
                    # | Atspi.KeyListenerSyncType.ALL_WINDOWS
                ),
            )

        logger.debug("Starting event loop")
        Atspi.event_main()
        logger.debug("Finished event loop")

    def stop(self):
        logger.debug("Deregistering listeners")

        Atspi.EventListener.deregister(
            self.listener, "object:state-changed:focused"
        )

        if self.key_listener:
            for modmask in MOD_MASKS:
                Atspi.deregister_keystroke_listener(
                    self.key_listener,
                    key_set=None,
                    modmask=modmask,
                    event_types=flags(
                        Atspi.KeyEventType.PRESSED,
                        Atspi.KeyEventType.RELEASED,
                    ),
                )

        logger.debug("Stopping event loop")
        Atspi.event_quit()

    def _on_focus_changed(self, event):
        self.text = ""
        is_focused = event.detail1 == 1
        if is_focused and event.source.role in TEXT_ENTRY_ROLES:
            logger.debug(
                "Focus source: source: %r, role: %r",
                event.source.name,
                event.source.role,
            )
            self.has_focus = True
            self.text_entry_focused.emit(event.source)
        elif self.has_focus:
            logger.debug(
                "No focus source: source: %r, focused: %r, role: %r",
                event.source.name,
                is_focused,
                event.source.role,
            )
            self.has_focus = False
            self.text_entry_focused.emit(None)

    def _on_key_press(self, event):
        key_event = KeyEvent(
            keycode=event.hw_code,
            pressed=(event.type == Atspi.EventType.KEY_PRESSED_EVENT),
            modifiers=modifier_list(event.modifiers),
            text=event.event_string,
            is_text=event.is_text,
        )
        self.key_event.emit(key_event)
        return key_event.consumed

    def _eventWrapper(self, event, callback):
        return callback(event)
