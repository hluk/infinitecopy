# SPDX-License-Identifier: LGPL-2.0-or-later
import logging
import sys

from PySide6.QtCore import QByteArray, QDataStream
from PySide6.QtNetwork import QLocalSocket

CONNECTION_TIMEOUT_MS = 4000
PRINT_COMMAND = 1
ERROR_COMMAND = 2
EXIT_COMMAND = 3

logger = logging.getLogger(__name__)


class Client:
    def __init__(self, socket=None):
        if socket:
            self.socket = socket
        else:
            self.socket = QLocalSocket()
            self.socket.readyRead.connect(self._on_ready_read)
            self.cmd = None
            self.length = None
            self.arg = None
        self.stream = QDataStream(self.socket)
        self.error = None
        self.exit_code = 0
        self.socket.errorOccurred.connect(self._on_error_occurred)

    def disconnect(self):
        self.socket.disconnectFromServer()

    def connect(self, serverName):
        self.socket.connectToServer(serverName)
        return self.socket.waitForConnected(CONNECTION_TIMEOUT_MS)

    def waitForDisconnected(self):
        self.socket.waitForDisconnected(-1)

    def atEnd(self):
        return self.socket.atEnd()

    def waitForBytesAvailable(self):
        return (
            self.socket.bytesAvailable() > 0
            or self.socket.waitForReadyRead(-1)
        )

    def receive(self):
        if not self.waitForBytesAvailable():
            self.validate()

        length = self.stream.readUInt32()
        arg = QByteArray()
        arg.reserve(length)
        while self.waitForBytesAvailable():
            available = self.socket.bytesAvailable()
            to_read = length - arg.length()
            data = self.socket.read(to_read)
            arg.append(data)
            if available >= to_read:
                return arg

        self.validate()
        return None

    def send(self, arg):
        if isinstance(arg, str):
            arg = QByteArray(arg.encode("utf-8"))
        elif isinstance(arg, bytes):
            arg = QByteArray(arg)
        elif not isinstance(arg, QByteArray):
            raise RuntimeError(f"Can send only bytes, not an object: {arg!r}")

        self.stream.writeBytes(arg)
        self.validate()

    def sendCommand(self, cmd, arg):
        self.stream.writeUInt8(cmd)
        self.send(arg)

    def receiveCommand(self):
        if self.cmd is None:
            self.cmd = self.stream.readUInt8()

        if self.length is None:
            if not self.socket.bytesAvailable():
                return None, None
            self.length = self.stream.readUInt32()
            self.arg = QByteArray()
            self.arg.reserve(self.length)

        available = self.socket.bytesAvailable()
        to_read = self.length - self.arg.length()
        data = self.socket.read(to_read)
        self.arg.append(data)
        if available < to_read:
            return None, None

        cmd = self.cmd
        arg = self.arg
        self.cmd = None
        self.length = None
        self.arg = None

        return cmd, arg

    def sendPrint(self, arg):
        self.sendCommand(PRINT_COMMAND, arg)

    def sendError(self, arg):
        self.sendCommand(ERROR_COMMAND, arg)

    def sendExit(self, exit_code):
        self.sendCommand(EXIT_COMMAND, str(exit_code))

    def validate(self):
        if self.stream.status() != QDataStream.Ok:
            raise RuntimeError(
                f"Failed to send/receive data: {self.stream.status()}"
                f"\nError: {self.socket.error()}"
            )

    def _on_error_occurred(self):
        self.error = f"Error: {self.socket.error()}"
        self.disconnect()

    def _on_ready_read(self):
        while self.socket.bytesAvailable() > 0:
            cmd, arg = self.receiveCommand()
            if cmd is None:
                return

            if cmd == PRINT_COMMAND:
                sys.stdout.buffer.write(bytes(arg))
                sys.stdout.buffer.flush()
            elif cmd == ERROR_COMMAND:
                text = bytes(arg).decode("utf-8")
                self.error = f"Error: {text}"
                self.disconnect()
            elif cmd == EXIT_COMMAND:
                self.exit_code = max(self.exit_code, int(arg))
                self.disconnect()
            else:
                self.error = f"Unknown message id {cmd}: {type(arg)}"
                self.disconnect()
