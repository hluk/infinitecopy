# SPDX-License-Identifier: LGPL-2.0-or-later
import logging

import infinitecopy.commands
from infinitecopy.Client import Client

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

    def receive(self, socket):
        client = Client(socket)
        try:
            self._on_message_helper(client)
        except Exception as e:
            logger.info("Client failure: %s", e)
            client.sendError(str(e))
        finally:
            if client.exit_code is None:
                client.sendExit(0)

    def _on_message_helper(self, client):
        command = client.receiveCommandName()
        logger.debug("Received command: %s", command)
        fn = self.commands.get(command)
        if fn:
            fn(self.app, client)
        else:
            raise RuntimeError(f"Unknown message received: {command}")
