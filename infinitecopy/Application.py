# SPDX-License-Identifier: LGPL-2.0-or-later
from PyQt5.QtCore import QSortFilterProxyModel, QUrl, qInfo, qWarning
from PyQt5.QtGui import QGuiApplication, QIcon
from PyQt5.QtQuick import QQuickView
from PyQt5.QtSql import QSqlDatabase

from infinitecopy.ClipboardFactory import createClipboard
from infinitecopy.ClipboardItemModel import ClipboardItemModel, Column
from infinitecopy.ClipboardItemModelImageProvider import (
    ClipboardItemModelImageProvider,
)
from infinitecopy.Server import Server


class ApplicationError(RuntimeError):
    pass


def pasterIfAvailable(view):
    try:
        from infinitecopy.Paster import Paster
    except (ImportError, ValueError) as e:
        qInfo(f"Pasting won't work: {e}")
        return None

    return Paster(view)


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
        self.filterProxyModel.setFilterKeyColumn(Column.TEXT)

        self.clipboard = createClipboard()
        self.clipboard.changed.connect(self.clipboardItemModel.addItem)

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

        self.paster = pasterIfAvailable(self.view)
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

    def _on_message(self, message):
        if message == "show":
            qInfo("Activating window")
            self.view.hide()
            self.view.show()
        else:
            qWarning(f"Unknown message received: {message}")
