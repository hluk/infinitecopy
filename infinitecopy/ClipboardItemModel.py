# SPDX-License-Identifier: LGPL-2.0-or-later
import hashlib

from PySide6.QtCore import QByteArray, QDateTime, Qt, Slot
from PySide6.QtSql import QSqlQuery, QSqlTableModel

import infinitecopy.MimeFormats as formats

COLUMN_TEXT = 2
SQL_CREATE_TABLE_ITEM = """
CREATE TABLE IF NOT EXISTS item (
    copyTime TIMESTAMP NOT NULL,
    itemHash TEXT PRIMARY KEY ON CONFLICT REPLACE,
    itemText TEXT
) WITHOUT ROWID;
"""

SQL_CREATE_TABLE_DATA = """
CREATE TABLE IF NOT EXISTS data (
    itemHash TEXT NOT NULL,
    format TEXT NOT NULL,
    bytes BLOB NOT NULL,
    FOREIGN KEY(itemHash) REFERENCES item(itemHash)
        ON DELETE CASCADE
);
"""

SQL_CREATE_DB = [
    "PRAGMA foreign_keys = ON;",
    SQL_CREATE_TABLE_ITEM,
    SQL_CREATE_TABLE_DATA,
    "CREATE INDEX IF NOT EXISTS index_item_text ON item (itemText);",
    "CREATE INDEX IF NOT EXISTS index_data_itemHash ON data (itemHash);",
]

SQL_SELECT_DATA = (
    "SELECT bytes FROM data WHERE itemHash = :itemHash AND format = :format;"
)

SQL_SELECT_FORMAT_AND_DATA = (
    "SELECT format, bytes FROM data WHERE itemHash = :itemHash;"
)

SQL_SELECT_HAS_IMAGE = (
    "SELECT 1 FROM data WHERE itemHash = :itemHash AND format = :format;"
)

SQL_INSERT_DATA = (
    "INSERT INTO data (itemHash, format, bytes)"
    " VALUES (:itemHash, :format, :bytes);"
)


def createHash(data):
    hash_ = hashlib.sha256()

    for format_ in data:
        hash_.update(format_.encode("utf-8"))
        hash_.update(b";;")
        hash_.update(data[format_])

    return hash_.hexdigest()


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
    def __init__(self, db):
        QSqlTableModel.__init__(self, db=db)
        self.roles = {}
        self.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.lastAddedHash = ""
        self.generateRoleNames()

    def create(self):
        self.beginTransaction()

        query = QSqlQuery(self.database())
        for statement in SQL_CREATE_DB:
            prepareQuery(query, statement)
            executeQuery(query)

        self.endTransaction()

        self.setTable("item")
        self.setSort(0, Qt.DescendingOrder)
        self.select()

    def addItemNoEmpty(self, data):
        # Ignore empty data.
        if all(d.trimmed().length() == 0 for d in data.values()):
            return

        self.beginTransaction()
        self.addItemNoCommit(data)
        self.endTransaction()
        self.submitChanges()

    def addItemNoCommit(self, data):
        itemHash = createHash(data)
        if self.lastAddedHash == itemHash:
            return False

        self.lastAddedHash = itemHash

        text = data.get(formats.mimeText, QByteArray())

        record = self.record()
        record.setValue("itemHash", itemHash)
        record.setValue("itemText", text)
        record.setValue("copyTime", QDateTime.currentDateTime())

        if not self.insertRecord(0, record):
            raise ValueError(
                f"Failed to insert item: {self.lastError().text()}"
            )

        for format_, bytes_ in data.items():
            if format_ == formats.mimeText:
                continue

            query = QSqlQuery(self.database())
            prepareQuery(query, SQL_INSERT_DATA)
            query.bindValue(":itemHash", itemHash)
            query.bindValue(":format", format_)
            query.bindValue(":bytes", bytes_)
            executeQuery(query)

        return True

    def submitChanges(self):
        if not self.submitAll():
            raise ValueError(
                f"Failed submit queries: {self.lastError().text()}"
            )

    def beginTransaction(self):
        self.database().transaction()

    def endTransaction(self):
        if not self.database().commit():
            raise ValueError(
                f"Failed submit queries: {self.lastError().text()}"
            )

    @Slot(int)
    def removeItem(self, row):
        if self.removeRow(row):
            self.submitChanges()

    def generateRoleNames(self):
        self.roles = super().roleNames()
        role = Qt.UserRole + 1

        self.copyTimeRole = role
        self.roles[role] = b"copyTime"
        role += 1

        self.itemTextRole = role
        self.roles[role] = b"itemText"
        role += 1

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
        if role < Qt.UserRole:
            return QSqlTableModel.data(self, index, role)

        record = self.record(index.row())

        if role == self.copyTimeRole:
            return record.value("copyTime")

        if role == self.itemTextRole:
            return record.value("itemText")

        if role == self.itemHtmlRole:
            query = QSqlQuery(self.database())
            prepareQuery(query, SQL_SELECT_DATA)
            query.bindValue(":itemHash", record.value("itemHash"))
            query.bindValue(":format", formats.mimeHtml)
            executeQuery(query)
            if query.next():
                return query.value("bytes")
            return ""

        if role == self.itemHasImageRole:
            query = QSqlQuery(self.database())
            prepareQuery(query, SQL_SELECT_HAS_IMAGE)
            query.bindValue(":itemHash", record.value("itemHash"))
            query.bindValue(":format", formats.mimePng)
            executeQuery(query)
            return query.next()

        if role == self.itemDataRole:
            query = QSqlQuery(self.database())
            prepareQuery(query, SQL_SELECT_FORMAT_AND_DATA)
            query.bindValue(":itemHash", record.value("itemHash"))
            executeQuery(query)
            data = {}
            while query.next():
                data[query.value("format")] = query.value("bytes")
            return data

        return None

    def imageData(self, row):
        record = self.record(row)
        query = QSqlQuery(self.database())
        prepareQuery(query, SQL_SELECT_DATA)
        query.bindValue(":itemHash", record.value("itemHash"))
        query.bindValue(":format", formats.mimePng)
        executeQuery(query)
        if query.next():
            return query.value(0)
        return None
