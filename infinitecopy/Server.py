# SPDX-License-Identifier: LGPL-2.0-or-later
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtNetwork import QLocalServer


class Server(QObject):
    messageReceived = pyqtSignal(str)

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

        message = bytes(socket.readAll()).decode("utf-8")
        self.messageReceived.emit(message)