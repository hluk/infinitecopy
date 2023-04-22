# SPDX-License-Identifier: LGPL-2.0-or-later
import logging

from PySide6.QtCore import QByteArray, QDataStream
from PySide6.QtNetwork import QLocalSocket

CONNECTION_TIMEOUT_MS = 4000

logger = logging.getLogger(__name__)


class Client:
    def __init__(self):
        self.socket = QLocalSocket()
        self.socket.readyRead.connect(self._on_ready_read)
        self.stream = QDataStream(self.socket)

    def connect(self, serverName):
        self.socket.connectToServer(serverName)
        return self.socket.waitForConnected(CONNECTION_TIMEOUT_MS)

    def waitForDisconnected(self):
        self.socket.waitForDisconnected(-1)

    def _on_ready_read(self):
        while self.socket.bytesAvailable() > 0:
            obj = self.stream.readQVariant()
            if isinstance(obj, QByteArray):
                print(bytes(obj).decode("utf-8"), end="")
            elif isinstance(obj, str):
                print(obj, end="")
            elif isinstance(obj, Exception):
                raise obj
            else:
                logger.error("Unknown message type: %s", type(obj))
