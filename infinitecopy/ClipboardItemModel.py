# SPDX-License-Identifier: LGPL-2.0-or-later
import hashlib

from PyQt5.QtCore import QByteArray, QDateTime, Qt, pyqtSlot
from PyQt5.QtSql import QSqlQuery, QSqlTableModel

import infinitecopy.MimeFormats as formats
from infinitecopy.serialize import deserializeData, serializeData

SQL_CREATE_TABLE_ITEM = """
CREATE TABLE IF NOT EXISTS item (
    copyTime TIMESTAMP NOT NULL,
    itemHash TEXT NOT NULL UNIQUE ON CONFLICT REPLACE,
    itemText TEXT NOT NULL,
    itemData BLOB
);
"""

SQL_CREATE_DB = [
    SQL_CREATE_TABLE_ITEM,
    "CREATE INDEX IF NOT EXISTS index_item_text ON item (itemText);",
]


class Column:
    TIMESTAMP = 0
    HASH = 1
    TEXT = 2
    DATA = 3


def createHash(data):
    hash = hashlib.sha256()

    for format in data:
        hash.update(format.encode("utf-8"))
        hash.update(b";;")
        hash.update(data[format])

    return hash.hexdigest()


def prepareQuery(query, queryText):
    if not query.prepare(queryText):
        raise ValueError(
            "Bad query template: {}\nLast error: {}".format(
                queryText, query.lastError().text()
            )
        )


def executeQuery(query):
    if not query.exec_():
        raise ValueError(
            "Failed to execute query: {}\nLast error: {}".format(
                query.lastQuery(), query.lastError().text()
            )
        )


class ClipboardItemModel(QSqlTableModel):
    def __init__(self):
        QSqlTableModel.__init__(self)
        self.roles = {}
        self.setEditStrategy(QSqlTableModel.EditStrategy.OnManualSubmit)
        self.lastAddedHash = ""

    def create(self):
        self.database().transaction()

        query = QSqlQuery()
        for statement in SQL_CREATE_DB:
            prepareQuery(query, statement)
            executeQuery(query)

        self.database().commit()

        self.setTable("item")
        self.setSort(0, Qt.SortOrder.DescendingOrder)
        self.select()
        self.generateRoleNames()

    def addItemNoEmpty(self, data):
        # Ignore empty data.
        if all(d.trimmed().length() == 0 for d in data.values()):
            return

        if self.addItemNoCommit(data):
            self.submitChanges()

    def addItemNoCommit(self, data):
        hash = createHash(data)
        if self.lastAddedHash == hash:
            return False

        self.lastAddedHash = hash

        text = data.get(formats.mimeText, QByteArray())

        record = self.record()
        record.setValue("itemHash", hash)
        record.setValue("itemText", text)
        record.setValue("itemData", QByteArray(serializeData(data)))
        record.setValue("copyTime", QDateTime.currentDateTime())

        if not self.insertRecord(0, record):
            raise ValueError(
                "Failed to insert item: " + self.lastError().text()
            )

        return True

    def submitChanges(self):
        if not self.submitAll():
            raise ValueError(
                "Failed submit queries: " + self.lastError().text()
            )

    def beginTransaction(self):
        self.database().transaction()

    def endTransaction(self):
        if not self.database().commit():
            raise ValueError(
                "Failed submit queries: " + self.lastError().text()
            )

    @pyqtSlot(int)
    def removeItem(self, row):
        self.beginTransaction()
        self.removeRow(row)

    def generateRoleNames(self):
        self.roles = {}
        for i in range(self.columnCount()):
            self.roles[Qt.ItemDataRole.UserRole + i + 1] = self.headerData(
                i, Qt.Orientation.Horizontal
            ).encode()

        role = Qt.ItemDataRole.UserRole + self.columnCount()
        self.itemHtmlRole = role
        self.roles[role] = b"itemHtml"
        role += 1

        self.itemHasImageRole = role
        self.roles[role] = b"hasImage"
        role += 1

        self.itemDataRole = role
        self.roles[role] = b"itemData"
        role += 1

    def roleNames(self):
        return self.roles

    def data(self, index, role):
        if role < Qt.ItemDataRole.UserRole:
            return QSqlTableModel.data(self, index, role)

        record = self.record(index.row())

        if role < Qt.ItemDataRole.UserRole + self.columnCount():
            column = role - Qt.ItemDataRole.UserRole - 1
            return record.value(column)

        dataValue = record.value("itemData")
        data = deserializeData(dataValue)

        if role == self.itemHtmlRole:
            return data.get(formats.mimeHtml, "")

        if role == self.itemHasImageRole:
            return formats.mimePng in data

        if role == self.itemDataRole:
            return data

        return None

    def imageData(self, row):
        record = self.record(row)
        dataValue = record.value("itemData")
        data = deserializeData(dataValue)

        if formats.mimePng in data:
            return data[formats.mimePng]

        return None
