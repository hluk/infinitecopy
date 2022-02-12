import hashlib
import pickle

from PyQt5.QtCore import (
    QBuffer,
    QByteArray,
    QDateTime,
    Qt,
    pyqtProperty,
    pyqtSlot,
)
from PyQt5.QtGui import QImage
from PyQt5.QtSql import QSqlDatabase, QSqlQuery, QSqlRecord, QSqlTableModel

from infinitecopy.MimeFormats import *


def createHash(data):
    hash = hashlib.md5()

    for format in data:
        hash.update(format.encode("utf-8"))
        hash.update(b";;")
        hash.update(data[format])

    return hash.hexdigest()


def serializeData(data):
    return pickle.dumps(data)


def deserializeData(bytes):
    try:
        return pickle.loads(bytes)
    except EOFError:
        return {}
    except TypeError:
        return {}


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

        text = data.get(mimeText, "")

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
            return data.get(mimeHtml, "")

        if role == self.itemHasImage:
            return mimePng in data

        return None

    def imageData(self, row):
        record = self.record(row)
        dataValue = record.value("itemData")
        data = deserializeData(dataValue)

        if mimePng in data:
            return data[mimePng]

        return None
