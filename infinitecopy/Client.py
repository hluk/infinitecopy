# SPDX-License-Identifier: LGPL-2.0-or-later
from PyQt5.QtNetwork import QLocalSocket

CONNECTION_TIMEOUT_MS = 4000


class Client:
    def __init__(self):
        self.socket = QLocalSocket()

    def connect(self, serverName):
        self.socket.connectToServer(serverName)
        return self.socket.waitForConnected(CONNECTION_TIMEOUT_MS)

    def send(self, message):
        self.socket.write(message.encode("utf-8"))
        self.socket.flush()
