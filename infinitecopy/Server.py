# SPDX-License-Identifier: LGPL-2.0-or-later
from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer

from infinitecopy.serialize import deserializeData


class Server(QObject):
    messageReceived = Signal(list)

    def __init__(self):
        super().__init__()
        self.server = QLocalServer()
        self.server.newConnection.connect(self._onNewConnection)

    def start(self, serverName):
        QLocalServer.removeServer(serverName)
        return self.server.listen(serverName)

    def _onNewConnection(self):
        socket = self.server.nextPendingConnection()
        if not socket:
            return

        def on_ready_read():
            commands = deserializeData(socket.readAll())
            self.messageReceived.emit(commands)

        socket.readyRead.connect(on_ready_read)
        socket.waitForDisconnected()
