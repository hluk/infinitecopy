# SPDX-License-Identifier: LGPL-2.0-or-later
import hashlib

from PySide6.QtCore import Property, QByteArray, QDateTime, Qt, Slot
from PySide6.QtSql import QSqlField, QSqlQuery, QSqlTableModel

import infinitecopy.MimeFormats as formats

FORMAT_TO_ITEM_COLUMN_MAP = {
    formats.mimeText: ":text",
    formats.mimeSource: ":source",
}

COLUMN_HASH = "hash"
COLUMN_TEXT = "text"
SQL_CREATE_TABLE_ITEM = f"""
CREATE TABLE IF NOT EXISTS item (
    id INTEGER PRIMARY KEY,
    createdTime TIMESTAMP NOT NULL,
    {COLUMN_HASH} TEXT,
    {COLUMN_TEXT} TEXT,
    source TEXT
);
"""

SQL_CREATE_TABLE_DATA = """
CREATE TABLE IF NOT EXISTS data (
    itemId INTEGER NOT NULL,
    format TEXT NOT NULL,
    bytes BLOB NOT NULL,
    FOREIGN KEY(itemId) REFERENCES item(id)
        ON DELETE CASCADE
);
"""

SQL_CREATE_DB = [
    "PRAGMA foreign_keys = ON;",
    SQL_CREATE_TABLE_ITEM,
    SQL_CREATE_TABLE_DATA,
    "CREATE INDEX IF NOT EXISTS index_item_hash ON item (hash);",
    "CREATE INDEX IF NOT EXISTS index_data_item_id ON data (itemId);",
]

SQL_SELECT_DATA = (
    "SELECT bytes FROM data WHERE itemId = :id AND format = :format;"
)

SQL_SELECT_FORMAT_AND_DATA = (
    "SELECT format, bytes FROM data WHERE itemId = :id;"
)

SQL_HAS_FORMAT = "SELECT 1 FROM data WHERE itemId = :id AND format = :format;"

SQL_INSERT_ITEM = (
    "INSERT INTO item (createdTime, hash, text, source)"
    " VALUES (:createdTime, :hash, :text, :source);"
)

SQL_INSERT_DATA = (
    "INSERT INTO data (itemId, format, bytes)"
    " VALUES (:itemId, :format, :bytes);"
)


def createHash(data):
    hash_ = hashlib.sha256()

    for format_ in data:
        if format_.startswith(formats.mimePrefixInternal):
            continue

        hash_.update(format_.encode("utf-8"))
        hash_.update(b";;")
        hash_.update(data[format_])

    return hash_.hexdigest()


def prepareQuery(query, queryText):
    if not query.prepare(queryText):
        lastError = query.lastError().text()
        raise ValueError(
            f"Bad query template: {queryText}\nLast error: {lastError}"
        )


def executeQuery(query):
    if not query.exec():
        lastQuery = query.lastQuery()
        lastError = query.lastError().text()
        raise ValueError(
            f"Failed to execute query: {lastQuery}\nLast error: {lastError}"
        )


class ClipboardItemModel(QSqlTableModel):
    def __init__(self, db):
        QSqlTableModel.__init__(self, db=db)
        self.roles = {}
        self.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.lastAddedHash = ""
        self.generateRoleNames()

    @Property(int)
    def textColumn(self):
        return self.fieldIndex(COLUMN_TEXT)

    @Property(int)
    def hashColumn(self):
        return self.fieldIndex(COLUMN_HASH)

    def setTextFilter(self, needle):
        if not needle:
            self.setFilter("")
            return

        f = QSqlField("", str)
        if "%" in needle:
            f.setValue(needle)
        else:
            f.setValue(f"%{needle}%")

        formatted = self.database().driver().formatValue(f)
        condition = f"{COLUMN_TEXT} LIKE {formatted}"

        if needle.islower():
            self.database().exec("PRAGMA case_sensitive_like=OFF;")
        else:
            self.database().exec("PRAGMA case_sensitive_like=ON;")

        self.setFilter(condition)
        self.select()

    textFilter = Property(str, None, setTextFilter)

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
        if all(
            f.startswith(formats.mimePrefixInternal)
            or d.trimmed().length() == 0
            for f, d in data.items()
        ):
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

        query = QSqlQuery(self.database())
        prepareQuery(query, SQL_INSERT_ITEM)
        query.bindValue(":hash", itemHash)
        query.bindValue(":createdTime", QDateTime.currentDateTime())
        for format_, column in FORMAT_TO_ITEM_COLUMN_MAP.items():
            value = data.get(format_, QByteArray())
            query.bindValue(column, value)
        executeQuery(query)
        itemId = query.lastInsertId()

        for format_, bytes_ in data.items():
            if format_ in FORMAT_TO_ITEM_COLUMN_MAP:
                continue

            query = QSqlQuery(self.database())
            prepareQuery(query, SQL_INSERT_DATA)
            query.bindValue(":itemId", itemId)
            query.bindValue(":format", format_)
            query.bindValue(":bytes", bytes_)
            executeQuery(query)

        return True

    def submitChanges(self):
        if not self.submitAll():
            self.revertAll()
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

    @Slot(int, int)
    def removeItems(self, row, count):
        if self.removeRows(row, count):
            self.submitChanges()

    def generateRoleNames(self):
        self.roles = super().roleNames()
        role = Qt.UserRole + 1

        self.itemIdRole = role
        self.roles[role] = b"itemId"
        role += 1

        self.createdTimeRole = role
        self.roles[role] = b"createdTime"
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

        self.itemSourceRole = role
        self.roles[role] = b"itemSource"
        role += 1

        self.itemHashRole = role
        self.roles[role] = b"itemHash"
        role += 1

    def roleNames(self):
        return self.roles

    def data(self, index, role):
        if role < Qt.UserRole:
            return QSqlTableModel.data(self, index, role)

        record = self.record(index.row())

        if role == self.itemIdRole:
            return record.value("id")

        if role == self.createdTimeRole:
            return record.value("createdTime")

        if role == self.itemTextRole:
            return record.value("text")

        if role == self.itemHashRole:
            return record.value("hash")

        if role == self.itemSourceRole:
            return record.value("source")

        if role == self.itemHtmlRole:
            query = self.executeQuery(
                SQL_SELECT_DATA,
                id=record.value("id"),
                format=formats.mimeHtml,
            )
            if query.next():
                return query.value("bytes")
            return ""

        if role == self.itemHasImageRole:
            query = self.executeQuery(
                SQL_SELECT_DATA,
                id=record.value("id"),
                format=formats.mimePng,
            )
            return query.next()

        if role == self.itemDataRole:
            query = self.executeQuery(
                SQL_SELECT_FORMAT_AND_DATA, id=record.value("id")
            )

            data = {}
            while query.next():
                data[query.value("format")] = query.value("bytes")

            text = record.value("text")
            if text:
                data[formats.mimeText] = text

            return data

        return None

    def imageData(self, row):
        record = self.record(row)
        query = self.executeQuery(
            SQL_SELECT_DATA, id=record.value("id"), format=formats.mimePng
        )
        if query.next():
            return query.value(0)
        return None

    def executeQuery(self, queryText: str, **kwargs):
        query = QSqlQuery(self.database())
        prepareQuery(query, queryText)
        for name, value in kwargs.items():
            query.bindValue(f":{name}", value)
        executeQuery(query)
        return query
