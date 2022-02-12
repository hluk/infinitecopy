#!/usr/bin/env python
import sys

from PyQt5.QtCore import (
    QDir,
    QSortFilterProxyModel,
    QStandardPaths,
    QUrl,
    qInfo,
)
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlComponent
from PyQt5.QtQuick import QQuickView
from PyQt5.QtSql import QSqlDatabase

from infinitecopy.Clipboard import Clipboard
from infinitecopy.ClipboardItemModel import ClipboardItemModel
from infinitecopy.ClipboardItemModelImageProvider import (
    ClipboardItemModelImageProvider,
)
from infinitecopy.MimeFormats import *


def openDataBase():
    db = QSqlDatabase.addDatabase("QSQLITE")
    dataPath = QStandardPaths.writableLocation(
        QStandardPaths.AppLocalDataLocation
    )
    if not QDir(dataPath).mkpath("."):
        raise Exception("Failed to create data directory {}".format(dataPath))

    dbPath = dataPath + "/infinitecopy_items.sql"
    qInfo('Using item database "{}".'.format(dbPath))
    db.setDatabaseName(dbPath)
    db.open()


def main():
    app = QGuiApplication(sys.argv)
    app.setApplicationName("InfiniteCopy")
    app.setApplicationDisplayName("InfiniteCopy")

    openDataBase()

    view = QQuickView()

    clipboardItemModel = ClipboardItemModel()
    clipboardItemModel.create()

    filterProxyModel = QSortFilterProxyModel()
    filterProxyModel.setSourceModel(clipboardItemModel)

    clipboard = Clipboard()
    clipboard.setFormats([mimeText, mimeHtml, mimePng, mimeSvg])
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

    view.setSource(QUrl.fromLocalFile("qml/MainWindow.qml"))
    view.setGeometry(100, 100, 400, 240)
    view.show()

    engine.quit.connect(QGuiApplication.quit)

    return app.exec_()


if __name__ == "__main__":
    main()
