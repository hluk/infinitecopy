# SPDX-License-Identifier: LGPL-2.0-or-later
import logging
import sys
from enum import IntEnum

from PySide6.QtCore import QByteArray, QDataStream
from PySide6.QtNetwork import QLocalSocket

logger = logging.getLogger(__name__)

CONNECTION_TIMEOUT_MS = 4000


class MessageId(IntEnum):
    PRINT = 1
    ERROR = 2
    EXIT = 3
    COMMAND_NAME = 4
    COMMAND_ARG = 5
    COMMAND_END = 6


class Client:
    def __init__(self, socket=None, log_states=True):
        if socket:
            self.socket = socket
        else:
            self.socket = QLocalSocket()
            self.socket.readyRead.connect(self._on_ready_read)

        self.msg_id = None
        self.length = None
        self.arg = None
        self.stream = QDataStream(self.socket)
        self.error = None
        self.exit_code = 0
        self.log_states = log_states
        self.socket.stateChanged.connect(self._on_state_changed)
        self.socket.errorOccurred.connect(self._on_error_occurred)

    def disconnect(self):
        self.socket.disconnectFromServer()

    def connect(self, serverName):
        self.socket.connectToServer(serverName)
        return self.socket.waitForConnected(CONNECTION_TIMEOUT_MS)

    def waitForDisconnected(self):
        self.socket.waitForDisconnected(-1)

    def waitForBytesAvailable(self):
        return (
            self.socket.bytesAvailable() > 0
            or self.socket.waitForReadyRead(-1)
        )

    def receiveCommandArguments(self):
        while True:
            msg_id, arg = self._receive(
                MessageId.COMMAND_ARG, MessageId.COMMAND_END
            )

            if msg_id == MessageId.COMMAND_END:
                break

            if msg_id != MessageId.COMMAND_ARG:
                self.error = f"Expected argument but got message ID {msg_id}"
                logger.error(self.error)
                self.disconnect()
                break

            yield arg

    def receiveCommandName(self):
        _msg_id, name = self._receive(MessageId.COMMAND_NAME)
        return bytes(name).decode("utf-8")

    def sendCommandArgument(self, arg):
        self._send(MessageId.COMMAND_ARG, arg)

    def sendCommandName(self, arg):
        self._send(MessageId.COMMAND_NAME, arg)

    def sendCommandEnd(self):
        self._send(MessageId.COMMAND_END, b"")

    def _send(self, msg_id, arg):
        if isinstance(arg, str):
            arg = QByteArray(arg.encode("utf-8"))
        elif isinstance(arg, bytes):
            arg = QByteArray(arg)
        elif not isinstance(arg, QByteArray):
            raise RuntimeError(f"Can send only bytes, not an object: {arg!r}")

        self.stream.writeUInt8(msg_id)
        self.stream.writeBytes(arg)
        self.validate()

    def _receive(self, *expected_msg_ids):
        while self.waitForBytesAvailable():
            msg_id, arg = self._tryReceive()
            if msg_id is None:
                continue

            if msg_id not in expected_msg_ids:
                self.error = f"Unexpected message ID {msg_id} (expected {expected_msg_ids})"
                logger.error(self.error)
                self.disconnect()
                return None, None

            return msg_id, arg

        self.error = "Failed to receive message"
        logger.error(self.error)
        self.disconnect()
        return None, None

    def _tryReceive(self):
        if self.msg_id is None:
            self.msg_id = self.stream.readUInt8()

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

        msg_id = self.msg_id
        arg = self.arg
        self.msg_id = None
        self.length = None
        self.arg = None

        return msg_id, arg

    def sendPrint(self, arg):
        self._send(MessageId.PRINT, arg)

    def sendError(self, arg):
        self._send(MessageId.ERROR, arg)

    def sendExit(self, exit_code):
        self._send(MessageId.EXIT, str(exit_code))

    def validate(self):
        if self.stream.status() != QDataStream.Ok:
            raise RuntimeError(
                f"Failed to send/receive data: {self.stream.status()}"
                f"\nError: {self.socket.error()}"
            )

    def _on_state_changed(self, state):
        if self.log_states:
            logger.debug("Client state changed: %s", state)

    def _on_error_occurred(self):
        self.error = f"Error: {self.socket.error()}"
        if self.log_states:
            logger.warning("Client socket error: %s", self.error)
        self.disconnect()

    def _on_ready_read(self):
        while self.socket.bytesAvailable() > 0:
            msg_id, arg = self._tryReceive()
            if msg_id is None:
                return

            if msg_id == MessageId.PRINT:
                logger.debug("Client print: %d bytes", len(arg))
                sys.stdout.buffer.write(bytes(arg))
                sys.stdout.buffer.flush()
            elif msg_id == MessageId.ERROR:
                text = bytes(arg).decode("utf-8")
                self.error = f"Error: {text}"
                self.disconnect()
            elif msg_id == MessageId.EXIT:
                self.exit_code = max(self.exit_code, int(arg))
                self.disconnect()
            else:
                self.error = f"Unknown message ID {msg_id}: {type(arg)}"
                self.disconnect()
