#!/usr/bin/env python
# SPDX-License-Identifier: LGPL-2.0-or-later
import sys
from pathlib import Path

from PyQt5.QtCore import (
    QDir,
    QSortFilterProxyModel,
    QStandardPaths,
    QUrl,
    qInfo,
)
from PyQt5.QtGui import QGuiApplication, QIcon
from PyQt5.QtQuick import QQuickView
from PyQt5.QtSql import QSqlDatabase

import infinitecopy.MimeFormats as formats
from infinitecopy.Clipboard import Clipboard
from infinitecopy.ClipboardItemModel import ClipboardItemModel, Column
from infinitecopy.ClipboardItemModelImageProvider import (
    ClipboardItemModelImageProvider,
)


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


def main():
    app = QGuiApplication(sys.argv)
    app.setApplicationName("InfiniteCopy")
    app.setApplicationDisplayName("InfiniteCopy")

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

    clipboard = Clipboard()
    clipboard.setFormats(
        [formats.mimeText, formats.mimeHtml, formats.mimePng, formats.mimeSvg]
    )
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

    view.setSource(QUrl.fromLocalFile(str(Path(qmlPath, "MainWindow.qml"))))
    view.setGeometry(100, 100, 400, 240)
    view.show()

    engine.quit.connect(QGuiApplication.quit)

    return app.exec_()


if __name__ == "__main__":
    main()
