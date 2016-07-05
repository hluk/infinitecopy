from PyQt5.QtCore import pyqtProperty, pyqtSlot, Qt, QDateTime
from PyQt5.QtSql import QSqlDatabase, QSqlQuery, QSqlRecord, QSqlTableModel

def prepareQuery(query, queryText):
    if not query.prepare(queryText):
        raise ValueError('Bad query template: {}\nLast error: {}'
                .format(queryText, query.lastError().text()))

def executeQuery(query):
    if not query.exec_():
        raise ValueError('Failed to execute query: {}\nLast error: {}'
                .format(query.lastQuery(), query.lastError().text()))

class ClipboardItemModel(QSqlTableModel):
    def __init__(self):
        QSqlTableModel.__init__(self)
        self.roles = {}
        self.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.lastAddedText = ""

    def create(self):
        try:
            QSqlDatabase.database().transaction();

            query = QSqlQuery()
            prepareQuery(query,
                """
                create table clipboardItems(
                    itemText text,
                    copyTime timestamp
                );
                """)
            executeQuery(query)
        except ValueError:
            pass
        finally:
            QSqlDatabase.database().commit();

        self.setTable('clipboardItems')
        self.setSort(1, Qt.DescendingOrder)
        self.select()
        self.generateRoleNames()

    def addItem(self, text):
        if text == "" or self.lastAddedText == text:
            return;

        self.lastAddedText = text

        record = self.record()
        record.setValue('itemText', text)
        record.setValue('copyTime', QDateTime.currentDateTime())

        if not self.insertRecord(0, record):
            raise ValueError('Failed to insert item: ' + self.lastError().text())

        self.submitChanges()

    def submitChanges(self):
        if not self.submitAll():
            raise ValueError('Failed submit queries: ' + self.lastError().text())

    @pyqtSlot(int)
    def removeItem(self, row):
        self.removeRow(row)
        self.submitChanges()

    def generateRoleNames(self):
        self.roles = {}
        for i in range(self.columnCount()):
            self.roles[Qt.UserRole + i + 1] = self.headerData(i, Qt.Horizontal).encode()

    def roleNames(self):
        return self.roles

    def data(self, index, role):
        if role < Qt.UserRole:
            return QSqlTableModel.data(self, index, role)

        column = role - Qt.UserRole - 1
        return self.record(index.row()).value(column)
