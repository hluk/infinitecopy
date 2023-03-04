# SPDX-License-Identifier: LGPL-2.0-or-later
import sys

from PySide6.QtCore import QByteArray, QSortFilterProxyModel, QUrl, qWarning
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQuick import QQuickView
from PySide6.QtSql import QSqlDatabase

import infinitecopy.MimeFormats as formats
from infinitecopy.ClipboardFactory import createClipboard
from infinitecopy.ClipboardItemModel import COLUMN_TEXT, ClipboardItemModel
from infinitecopy.ClipboardItemModelImageProvider import (
    ClipboardItemModelImageProvider,
)
from infinitecopy.Server import Server


class ApplicationError(RuntimeError):
    pass


def pasterIfAvailable():
    try:
        from infinitecopy.Paster import Paster
    except (ImportError, ValueError) as e:
        print(f"Pasting won't work: {e}", file=sys.stderr)
        return None

    return Paster()


class Application:
    def __init__(self, *, name, version, dbPath, serverName, args):
        self.app = QGuiApplication(args)
        self.app.setApplicationName(name)
        self.app.setApplicationDisplayName(name)
        self.app.setApplicationVersion(version)

        self.server = Server()
        if not self.server.start(serverName):
            raise ApplicationError(self.server.errorString())

        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName(dbPath)
        self.db.open()

        self.view = QQuickView()

        self.clipboardItemModel = ClipboardItemModel()
        self.clipboardItemModel.create()

        self.filterProxyModel = QSortFilterProxyModel()
        self.filterProxyModel.setSourceModel(self.clipboardItemModel)
        self.filterProxyModel.setFilterKeyColumn(COLUMN_TEXT)

        self.clipboard = createClipboard()
        self.clipboard.changed.connect(self.clipboardItemModel.addItemNoEmpty)

        self.engine = self.view.engine()

        self.imageProvider = ClipboardItemModelImageProvider(
            self.clipboardItemModel
        )
        self.engine.addImageProvider("items", self.imageProvider)

        self.context = self.view.rootContext()
        self.context.setContextProperty(
            "clipboardItemModel", self.clipboardItemModel
        )
        self.context.setContextProperty(
            "clipboardItemModelFilterProxy", self.filterProxyModel
        )
        self.context.setContextProperty("clipboard", self.clipboard)
        self.context.setContextProperty("view", self.view)

        self.paster = pasterIfAvailable()
        self.context.setContextProperty("paster", self.paster)

        self.engine.quit.connect(QGuiApplication.quit)

        self.server.messageReceived.connect(self._on_message)

    def setIcon(self, iconPath):
        self.app.setWindowIcon(QIcon(iconPath))

    def setMainWindowQml(self, path):
        self.view.setSource(QUrl.fromLocalFile(path))
        self.view.setGeometry(100, 100, 400, 240)

    def exec_(self):
        self.view.show()
        return self.app.exec_()

    def _on_message(self, commands):
        if commands == ["show"]:
            print("Activating window", file=sys.stderr)
            self.view.hide()
            self.view.show()
        elif commands[0] == "add":
            for text in commands[1:]:
                self.clipboardItemModel.addItemNoCommit(
                    {formats.mimeText: QByteArray(text.encode("utf-8"))}
                )
            self.clipboardItemModel.submitChanges()
        elif commands[0] == "paste":
            if self.paster is None:
                qWarning("Pasting text is unsupported")
            else:
                print("Pasting text", file=sys.stderr)
                for text in commands[1:]:
                    if not self.paster.paste(text):
                        qWarning("Failed to paste text")
                        break
        else:
            qWarning(f"Unknown message received: {commands}")
