#!/usr/bin/python3

from sys import argv
from os.path import join

from PyQt4.QtCore import (QDir, SIGNAL, Qt, QAbstractItemModel, QModelIndex,
                          QVariant)
from PyQt4.QtGui import (QDialog, QHBoxLayout, QWidget, QLabel, QStackedWidget,
                         QRadioButton, QLineEdit, QTreeView, QGridLayout,
                         QVBoxLayout, QPushButton, QFileSystemModel, 
                         QApplication, QTreeView)

from fathom import (get_sqlite3_database, get_postgresql_database, 
                    get_mysql_database)
from fathom.schema import Database

class QConnectionDialog(QDialog):
    
    '''
    General dialog for gathering information database connection.
    '''
    
    class PostgresWidget(QWidget):
        
        PARAMS = (("Host:", "host"), ("Port:", "port"),
                  ("Database name:", "databaseName"), 
                  ("User name:", "userName"), ("Password:", "password")) 
        
        def __init__(self, parent=None):
            QWidget.__init__(self, parent)
            
            grid = QGridLayout()            
            for index, (label, field) in enumerate(self.PARAMS):
                label = QLabel(self.tr(label))
                grid.addWidget(label, index, 0, Qt.AlignLeft | Qt.AlignTop)            
                setattr(self, field, QLineEdit())
                grid.addWidget(getattr(self, field), index, 1)

            self.setLayout(QVBoxLayout())
            self.layout().addLayout(grid)
            self.layout().addStretch()

        def validate(self):
            return bool(self.databaseName.text())
                
        def getDatabaseParams(self):
            result = []
            for label, field in (('dbname', self.databaseName),
                                 ('user', self.userName)):
                if field.text():
                    result.append('%s=%s' % (label, field.text()))
            return 'PostgreSQL', ' '.join(result)


    class SqliteWidget(QWidget):
        
        def __init__(self, parent=None):
            QWidget.__init__(self, parent)
            
            self.model = QFileSystemModel()
            self.model.setRootPath(QDir.currentPath())
            
            self.view = QTreeView(parent=self);
            self.view.setModel(self.model)
            for i in range(1, 4):
                self.view.header().hideSection(i)
            
            self.setLayout(QVBoxLayout())
            self.layout().addWidget(self.view)
            
        def validate(self):
            index = self.view.currentIndex()
            return bool(index.isValid()) and not self.model.isDir(index)
            
        def getDatabaseParams(self):
            index = self.view.currentIndex()
            result = []
            while index.isValid():
                result.append(unicode(index.data().toString()))
                index = index.parent()
            result.reverse()
            return 'sqlite3', join(*result)
            
    
    class MySqlWidget(QWidget):
        
        def __init__(self, parent=None):
            QWidget.__init__(self, parent)
        
    
    class OracleWidget(QWidget):

        PARAMS = (("User:", "user"), ("Password:", "password"),
                  ("Database source name:", "dsn"))
        
        def __init__(self, parent=None):
            QWidget.__init__(self, parent)
            
            grid = QGridLayout()
            for index, (label, field) in enumerate(self.PARAMS):
                label = QLabel(self.tr(label))
                grid.addWidget(label, index, 0, Qt.AlignLeft | Qt.AlignTop)            
                setattr(self, field, QLineEdit())
                grid.addWidget(getattr(self, field), index, 1)

            self.setLayout(QVBoxLayout())
            self.layout().addLayout(grid)
            self.layout().addStretch()


    def __init__(self, parent=None):
        QDialog.__init__(self)

        # preparing whole layout of dialog
        mainLayout = QVBoxLayout()
        widgetsLayout = QHBoxLayout()
        buttonsLayout = QHBoxLayout()
        radioLayout = QVBoxLayout()
        mainLayout.addLayout(widgetsLayout)
        mainLayout.addLayout(buttonsLayout)
        widgetsLayout.addLayout(radioLayout)
        
        # preparing radio buttons for choosing DBMS type
        radioLayout.addWidget(QLabel(self.tr("Database type:")))
        options = (('postgres', 'PostgreSQL', 'postgresChosen'), 
                   ('sqlite', 'sqlite3', 'sqliteChosen'),
                   ('oracle', 'Oracle', 'oracleChosen'),
                   ('mysql', 'MySQL', 'mysqlChosen'))
        for field, label, method in options:
            button = QRadioButton(self.tr(label), self)
            radioLayout.addWidget(button)
            self.connect(button, SIGNAL('pressed()'), getattr(self, method))
            setattr(self, field, button)
        radioLayout.addStretch()
        self.postgres.toggle()
        
        # preparing stack widgets for database connection details
        self.stackedWidget = QStackedWidget()
        self.stackedWidget.addWidget(self.PostgresWidget())
        self.stackedWidget.addWidget(self.SqliteWidget())
        self.stackedWidget.addWidget(self.OracleWidget())
        self.stackedWidget.addWidget(self.MySqlWidget())
        widgetsLayout.addWidget(self.stackedWidget)

        # preparing ok and cancel buttons at the bottom
        buttonsLayout.addStretch()
        for label, method in ('OK', self.accept), ('Cancel', self.reject):
            button = QPushButton(self.tr(label))
            self.connect(button, SIGNAL('pressed()'), method)
            buttonsLayout.addWidget(button)
        
        self.setLayout(mainLayout)
        self.resize(600, 300)
        
    def postgresChosen(self):
        self.stackedWidget.setCurrentIndex(0);
        
    def sqliteChosen(self):
        self.stackedWidget.setCurrentIndex(1);
    
    def oracleChosen(self):
        self.stackedWidget.setCurrentIndex(2);
        
    def mysqlChosen(self):
        self.stackedWidget.setCurrentIndex(3);
        
    def accept(self):
        if self.stackedWidget.currentWidget().validate():
            QDialog.accept(self)
            
    def getDatabaseParams(self):
        return self.stackedWidget.currentWidget().getDatabaseParams()


class FathomModel(QAbstractItemModel):
    
    def __init__(self, parent=None):
        QAbstractItemModel.__init__(self, parent)
        self._databases = []
        
    def addDatabase(self, database):
        self._databases.append(database)
        
    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        if parent.isValid():
            return QModelIndex()
        if len(self._databases) > row:
            print(row, column, 'creating nice index')
            return self.createIndex(row, column, self._databases[row])
        else:
            return QModelIndex()
            
    def parent(self, index):
        return QModelIndex()
            
    def rowCount(self, parent):
        if not parent.isValid():
            return len(self._databases)
        else:
            return 0
            
    def columnCount(self, parent):
        return 1
            
    def data(self, index, role):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        if index.internalPointer() is None:
            return ''
        return index.internalPointer().name

if __name__ == "__main__":
    app = QApplication(argv)
    view = QTreeView()
    model = FathomModel()
    model.addDatabase(get_postgresql_database('dbname=fathom username=fathom'))
    model.addDatabase(get_sqlite3_database('fathom.db3'))
    model.addDatabase(get_mysql_database(db='fathom', user='fathom'))
    view.setModel(model)
    view.show()
    app.exec()
