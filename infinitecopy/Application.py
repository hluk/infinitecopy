# SPDX-License-Identifier: LGPL-2.0-or-later
import logging

from PySide6.QtCore import QByteArray, QSortFilterProxyModel, QUrl
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQuick import QQuickView
from PySide6.QtSql import QSqlDatabase

import infinitecopy.MimeFormats as formats
from infinitecopy.ClipboardFactory import createClipboard
from infinitecopy.ClipboardItemModel import COLUMN_TEXT, ClipboardItemModel
from infinitecopy.ClipboardItemModelImageProvider import (
    ClipboardItemModelImageProvider,
)
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
        self.filterProxyModel.setFilterKeyColumn(COLUMN_TEXT)

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

        self.server.messageReceived.connect(self._on_message)

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

    def _on_message(self, commands):
        if commands == ["show"]:
            logger.debug("Activating window")
            self.view.hide()
            self.view.show()
        elif commands[0] == "add":
            self.clipboardItemModel.beginTransaction()
            for text in commands[1:]:
                self.clipboardItemModel.addItemNoCommit(
                    {formats.mimeText: QByteArray(text.encode("utf-8"))}
                )
            self.clipboardItemModel.endTransaction()
            self.clipboardItemModel.submitChanges()
        elif commands[0] == "paste":
            if self.paster is None:
                logger.warning("Pasting text is unsupported")
            else:
                logger.info("Pasting text")
                for text in commands[1:]:
                    if not self.paster.paste(text):
                        logger.warning("Failed to paste text")
                        break
        else:
            logger.warning(f"Unknown message received: {commands}")
