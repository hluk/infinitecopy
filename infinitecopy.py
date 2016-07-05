#!/usr/bin/env python
import sys

from PyQt5.QtCore import QSortFilterProxyModel, QUrl
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlComponent
from PyQt5.QtQuick import QQuickView
from PyQt5.QtSql import QSqlDatabase

from InfiniteCopy.ClipboardItemModel import ClipboardItemModel
from InfiniteCopy.Clipboard import Clipboard

def main():
    app = QGuiApplication(sys.argv)

    view = QQuickView()

    db = QSqlDatabase.addDatabase("QSQLITE")
    db.setDatabaseName('infinitecopy_items.sql')
    db.open()

    clipboardItemModel = ClipboardItemModel()
    clipboardItemModel.create()

    filterProxyModel = QSortFilterProxyModel()
    filterProxyModel.setSourceModel(clipboardItemModel)

    clipboard = Clipboard()
    clipboard.changed.connect(clipboardItemModel.addItem)

    context = view.rootContext()
    context.setContextProperty('clipboardItemModel', clipboardItemModel)
    context.setContextProperty('clipboardItemModelFilterProxy', filterProxyModel)
    context.setContextProperty('clipboard', clipboard)

    view.setSource(QUrl.fromLocalFile('qml/MainWindow.qml'))
    view.setGeometry(100, 100, 400, 240)
    view.show()

    engine = view.engine()
    engine.quit.connect(QGuiApplication.quit)

    return app.exec_()

if __name__ == '__main__':
    main()
