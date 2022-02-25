# SPDX-License-Identifier: LGPL-2.0-or-later
import hashlib

from PyQt5.QtCore import QByteArray, QDateTime, Qt, pyqtSlot
from PyQt5.QtSql import QSqlDatabase, QSqlQuery, QSqlTableModel

import infinitecopy.MimeFormats as formats
from infinitecopy.serialize import deserializeData, serializeData


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
        self.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.lastAddedHash = ""

    def create(self):
        try:
            QSqlDatabase.database().transaction()

            query = QSqlQuery()
            prepareQuery(
                query,
                """
                create table clipboardItems(
                    copyTime timestamp,
                    itemHash text,
                    itemText text,
                    itemData blob
                );
                """,
            )
            executeQuery(query)
        except ValueError:
            pass
        finally:
            QSqlDatabase.database().commit()

        self.setTable("clipboardItems")
        self.setSort(0, Qt.DescendingOrder)
        self.select()
        self.generateRoleNames()

    def addItem(self, data):
        # Ignore empty data.
        if all(d.trimmed().length() == 0 for d in data.values()):
            return

        hash = createHash(data)
        if self.lastAddedHash == hash:
            return

        self.lastAddedHash = hash

        query = QSqlQuery()
        prepareQuery(
            query,
            """
            delete from clipboardItems where itemHash = :hash;
            """,
        )
        query.bindValue(":hash", hash)
        executeQuery(query)

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

        self.submitChanges()

    def submitChanges(self):
        if not self.submitAll():
            raise ValueError(
                "Failed submit queries: " + self.lastError().text()
            )

    @pyqtSlot(int)
    def removeItem(self, row):
        self.removeRow(row)
        self.submitChanges()

    def generateRoleNames(self):
        self.roles = {}
        for i in range(self.columnCount()):
            self.roles[Qt.UserRole + i + 1] = self.headerData(
                i, Qt.Horizontal
            ).encode()

        role = Qt.UserRole + self.columnCount()
        self.itemHtmlRole = role
        self.roles[role] = b"itemHtml"
        role += 1

        self.itemHasImage = role
        self.roles[role] = b"hasImage"
        role += 1

        self.itemData = role
        self.roles[role] = b"itemData"
        role += 1

    def roleNames(self):
        return self.roles

    def data(self, index, role):
        if role < Qt.UserRole:
            return QSqlTableModel.data(self, index, role)

        record = self.record(index.row())

        if role < Qt.UserRole + self.columnCount():
            column = role - Qt.UserRole - 1
            return record.value(column)

        dataValue = record.value("itemData")
        data = deserializeData(dataValue)

        if role == self.itemHtmlRole:
            return data.get(formats.mimeHtml, "")

        if role == self.itemHasImage:
            return formats.mimePng in data

        if role == self.itemData:
            return data

        return None

    def imageData(self, row):
        record = self.record(row)
        dataValue = record.value("itemData")
        data = deserializeData(dataValue)

        if formats.mimePng in data:
            return data[formats.mimePng]

        return None
