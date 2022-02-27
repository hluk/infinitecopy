#!/usr/bin/env python
# SPDX-License-Identifier: LGPL-2.0-or-later
import argparse
import getpass
import sys
from pathlib import Path

from PyQt5.QtCore import (
    QCoreApplication,
    QDir,
    QSortFilterProxyModel,
    QStandardPaths,
    QUrl,
    qCritical,
    qInfo,
)
from PyQt5.QtGui import QGuiApplication, QIcon
from PyQt5.QtQuick import QQuickView
from PyQt5.QtSql import QSqlDatabase

from infinitecopy import __version__
from infinitecopy.Client import Client
from infinitecopy.ClipboardFactory import createClipboard
from infinitecopy.ClipboardItemModel import ClipboardItemModel, Column
from infinitecopy.ClipboardItemModelImageProvider import (
    ClipboardItemModelImageProvider,
)
from infinitecopy.Server import Server

APPLICATION_NAME = "InfiniteCopy"


def openDataBase():
    db = QSqlDatabase.addDatabase("QSQLITE")
    dataPath = QStandardPaths.writableLocation(
        QStandardPaths.AppLocalDataLocation
    )
    if not QDir(dataPath).mkpath("."):
        raise Exception(f"Failed to create data directory {dataPath}")

    dbPath = Path(dataPath, "infinitecopy_items.sql")
    qInfo(f'Using item database "{dbPath}"')
    db.setDatabaseName(str(dbPath))
    db.open()


def pasterIfAvailable(view):
    try:
        from infinitecopy.Paster import Paster
    except (ImportError, ValueError) as e:
        qInfo(f"Pasting won't work: {e}")
        return None

    return Paster(view)


def parse_argumments(args=None):
    parser = argparse.ArgumentParser(
        description=QCoreApplication.translate(
            "main", "Simple clipboard manager"
        )
    )
    parser.add_argument(
        QCoreApplication.translate("main", "commands"),
        nargs="*",
        help=QCoreApplication.translate(
            "main", "Commands to send to the application"
        ),
    )
    return parser.parse_args(args)


def main():
    args = parse_argumments()

    serverName = f"{APPLICATION_NAME}_{getpass.getuser()}"
    client = Client()
    if client.connect(serverName):
        client.send(" ".join(args.commands) or "show")
        return

    if args.commands:
        raise SystemExit("Start the application before using a command")

    app = QGuiApplication(sys.argv)
    app.setApplicationName(APPLICATION_NAME)
    app.setApplicationDisplayName(APPLICATION_NAME)
    app.setApplicationVersion(__version__)

    server = Server()
    if not server.start(serverName):
        qCritical(f"Failed to start app server: {server.errorString()}")
        return

    path = Path(__file__).parent
    qmlPath = Path(path, "qml")
    if not qmlPath.exists():
        path = path.parent
        qmlPath = Path(path, "qml")

    iconPath = Path(path, "infinitecopy.png")
    app.setWindowIcon(QIcon(str(iconPath)))

    openDataBase()

    view = QQuickView()

    clipboardItemModel = ClipboardItemModel()
    clipboardItemModel.create()

    filterProxyModel = QSortFilterProxyModel()
    filterProxyModel.setSourceModel(clipboardItemModel)
    filterProxyModel.setFilterKeyColumn(Column.TEXT)

    clipboard = createClipboard()
    clipboard.changed.connect(clipboardItemModel.addItem)

    engine = view.engine()

    imageProvider = ClipboardItemModelImageProvider(clipboardItemModel)
    engine.addImageProvider("items", imageProvider)

    context = view.rootContext()
    context.setContextProperty("clipboardItemModel", clipboardItemModel)
    context.setContextProperty(
        "clipboardItemModelFilterProxy", filterProxyModel
    )
    context.setContextProperty("clipboard", clipboard)
    context.setContextProperty("view", view)

    paster = pasterIfAvailable(view)
    context.setContextProperty("paster", paster)

    view.setSource(QUrl.fromLocalFile(str(Path(qmlPath, "MainWindow.qml"))))
    view.setGeometry(100, 100, 400, 240)
    view.show()

    engine.quit.connect(QGuiApplication.quit)

    def show():
        qInfo("Activating window")
        view.hide()
        view.show()

    server.messageReceived.connect(show)

    return app.exec_()


if __name__ == "__main__":
    main()
