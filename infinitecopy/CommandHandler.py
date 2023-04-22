# SPDX-License-Identifier: LGPL-2.0-or-later
import logging

import infinitecopy.commands

logger = logging.getLogger(__name__)


class CommandHandler:
    def __init__(self, app):
        self.app = app
        self.commands = {}

        for name, fn in infinitecopy.commands.__dict__.items():
            if name.startswith("command_") and callable(fn):
                prefix = len("command_")
                command_name = name[prefix:]
                self.commands[command_name] = fn

    def receive(self, stream, socket):
        try:
            self._on_message_helper(stream, socket)
        except Exception as e:
            logger.info("Client failure: %s", e)
            stream.writeQVariant(e)
        finally:
            socket.disconnectFromServer()

    def _on_message_helper(self, stream, socket):
        command = stream.readQVariant()
        callable = self.commands.get(command)
        if callable:
            callable(self.app, stream, socket)
        else:
            raise RuntimeError(f"Unknown message received: {command}")
