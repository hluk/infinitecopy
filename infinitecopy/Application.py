# SPDX-License-Identifier: LGPL-2.0-or-later
import logging

from PySide6.QtCore import QSortFilterProxyModel, QUrl
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQuick import QQuickView
from PySide6.QtSql import QSqlDatabase

from infinitecopy.ClipboardFactory import createClipboard
from infinitecopy.ClipboardItemModel import ClipboardItemModel
from infinitecopy.ClipboardItemModelImageProvider import (
    ClipboardItemModelImageProvider,
)
from infinitecopy.CommandHandler import CommandHandler
from infinitecopy.PluginManager import PluginManager
from infinitecopy.Server import Server

logger = logging.getLogger(__name__)


class ApplicationError(RuntimeError):
    pass


def pasterIfAvailable():
    try:
        from infinitecopy.Paster import Paster
    except (ImportError, ValueError) as e:
        logger.info(f"Pasting won't work: {e}")
        return None

    return Paster()


class Application:
    def __init__(
        self, *, name, version, dbPath, serverName, enable_pasting, args
    ):
        self.app = QGuiApplication(args)
        self.app.setApplicationName(name)
        self.app.setApplicationDisplayName(name)
        self.app.setApplicationVersion(version)

        self.server = Server()
        if not self.server.start(serverName):
            raise ApplicationError(self.server.errorString())

        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName(dbPath)
        if not self.db.open():
            raise ApplicationError(self.db.lastError().text())

        self.view = QQuickView()

        self.clipboardItemModel = ClipboardItemModel(self.db)
        self.clipboardItemModel.create()

        self.filterProxyModel = QSortFilterProxyModel()
        self.filterProxyModel.setSourceModel(self.clipboardItemModel)
        text_column = self.clipboardItemModel.textColumn
        self.filterProxyModel.setFilterKeyColumn(text_column)

        self.clipboard = createClipboard()

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

        self.paster = pasterIfAvailable() if enable_pasting else None
        self.context.setContextProperty("paster", self.paster)

        self.engine.quit.connect(QGuiApplication.quit)

        self.command_handler = CommandHandler(self)
        self.server.messageReceived.connect(self.command_handler.receive)

        self.plugin_manager = PluginManager(self)
        self.clipboard.changed.connect(self.plugin_manager.onClipboardChanged)
        if self.paster:
            self.paster.key_event.connect(self.plugin_manager.onKeyEvent)

    def setIcon(self, iconPath):
        self.app.setWindowIcon(QIcon(iconPath))

    def setMainWindowQml(self, path):
        self.view.setSource(QUrl.fromLocalFile(path))
        self.view.setGeometry(100, 100, 400, 240)

    def exec_(self):
        self.view.show()
        return self.app.exec_()
