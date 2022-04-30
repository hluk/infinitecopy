# SPDX-License-Identifier: LGPL-2.0-or-later
from PyQt5.QtNetwork import QLocalSocket

from infinitecopy.serialize import serializeData

CONNECTION_TIMEOUT_MS = 4000


class Client:
    def __init__(self):
        self.socket = QLocalSocket()

    def connect(self, serverName):
        self.socket.connectToServer(serverName)
        return self.socket.waitForConnected(CONNECTION_TIMEOUT_MS)

    def send(self, commands):
        self.socket.write(serializeData(commands))
        self.socket.flush()
