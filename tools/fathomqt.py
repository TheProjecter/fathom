#!/usr/bin/python3

from sys import argv
from os.path import join

from PyQt4.QtCore import (QDir, SIGNAL, Qt, QAbstractItemModel, QModelIndex,
                          QVariant, QCoreApplication, QEvent)
from PyQt4.QtGui import (QDialog, QHBoxLayout, QWidget, QLabel, QStackedWidget,
                         QRadioButton, QLineEdit, QTreeView, QGridLayout,
                         QVBoxLayout, QPushButton, QFileSystemModel, QIcon,
                         QApplication, QTreeView, QMainWindow, QAction,
                         QTabWidget, QMenu, QToolBar)

from fathom import (get_sqlite3_database, get_postgresql_database, 
                    get_mysql_database, TYPE_TO_FUNCTION)
from fathom.schema import Database

_ = lambda string: QCoreApplication.translate('', string)

class QClickableTabWidget(QTabWidget):

    def __init__(self, allowEmpty=True, parent=None):
        QTabWidget.__init__(self, parent)
        self._allowEmpty = allowEmpty
        self.installEventFilter(self)
        
    def eventFilter(self, target, event):
        if event.type() != QEvent.MouseButtonPress:
            return QTabWidget.eventFilter(self, target, event)
        position = event.pos()
        tab = -1
        for index in range(self.tabBar().count()):
            if self.tabBar().tabRect(index).contains(position):
                tab = index
                break
        if tab == -1:
            return QTabWidget.eventFilter(self, target, event)
        if event.button() == Qt.RightButton:
            menu = QMenu()
            actions = ((self.tr('Close'), 'triggered()', self.close),
                       (self.tr('Close other'), 'triggered()', self.closeOther))
            for title, signal, slot in actions:
                action = QAction(title, self)
                self.connect(action, SIGNAL(signal), slot)
                menu.addAction(action)
            self.selection = index
            menu.exec(event.globalPos())
            self.selection = None
            return True

    def close(self):
        if not self._allowEmpty and self.tabBar().count() == 1:
            return
        self.removeTab(self.selection)
        
    def closeOther(self):
        for i in range(self.selection):
            self.removeTab(0)
        while self.tabBar().count() > 1:
            self.removeTab(1)


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
                result.append(index.data())
                index = index.parent()
            result.reverse()
            return 'Sqlite3', join(*result)
            
    
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
            return QDialog.accept(self)
                        
    def getDatabaseParams(self):
        return self.stackedWidget.currentWidget().getDatabaseParams()


class FathomModel(QAbstractItemModel):
    
    class Item:
        
        def __init__(self, parent, row):
            self._parent = parent
            self._row = row
            
        def row(self):
            return self._row
            
        def parent(self):
            return self._parent
    
    class DatabaseItem(Item):
        
        def __init__(self, db, row):
            FathomModel.Item.__init__(self, None, row)
            self.db = db
            self.children = [FathomModel.TableListItem(list(db.tables.values()),
                                                       self, 0), 
                             FathomModel.ViewListItem(list(db.views.values()),
                                                      self, 1),
                             FathomModel.TriggerListItem(list(db.triggers.values()), 
                                                         self, 2)]

        def childrenCount(self):
            return 3
            
        def child(self, row):
            return self.children[row]
                             
        def name(self):
            return self.db.name

    
    class TableListItem(Item):
        
        def __init__(self, tables, parent, row):
            FathomModel.Item.__init__(self, parent, row)
            self._tables = tables
            Class = FathomModel.TableItem
            self.children = [Class(table, self, row) 
                             for row, table in enumerate(self._tables)]
        
        def childrenCount(self):
            return len(self._tables)
            
        def child(self, row):
            return self.children[row]
            
        def name(self):
            return _('Tables')


    class ViewListItem(Item):
        
        def __init__(self, views, parent, row):
            FathomModel.Item.__init__(self, parent, row)
            self._views = views

        def childrenCount(self):
            return 0
                        
        def name(self):
            return _('Views')
            
    
    class TriggerListItem(Item):
        
        def __init__(self, triggers, parent, row):
            FathomModel.Item.__init__(self, parent, row)
            self._triggers = triggers
            
        def childrenCount(self):
            return 0
            
        def name(self):
            return _('Triggers')


    class TableItem(Item):
        
        def __init__(self, table, parent, row):
            FathomModel.Item.__init__(self, parent, row)
            self._table = table
            
        def childrenCount(self):
            return 0
        
        def name(self):
            return self._table.name
            
        def createWidget(self):
            widget = QWidget()
            widget.setLayout(QVBoxLayout())
            widget.layout().addWidget(QLabel('<b>' + self._table.name + '</b>'))
            for column in self._table.columns.values():
                label = QLabel('%s: %s' % (column.name, column.type))
                widget.layout().addWidget(label)
            widget.layout().addStretch()
            return widget

    def __init__(self, parent=None):
        QAbstractItemModel.__init__(self, parent)
        self._databases = []
        
    def addDatabase(self, database):
        count = len(self._databases)
        self.beginInsertRows(QModelIndex(), count, count + 1)
        self._databases.append(self.DatabaseItem(database, 
                                                 len(self._databases)))
        self.endInsertRows()
        
    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        if parent.isValid():
            parent = parent.internalPointer()
            if parent.childrenCount() > row:
                return self.createIndex(row, column, parent.child(row))
            else:
                return QModelIndex()
        if len(self._databases) > row:
            return self.createIndex(row, column, self._databases[row])
        else:
            return QModelIndex()
            
    def parent(self, index):
        if not index.isValid() or index.internalPointer().parent() is None:
            return QModelIndex()
        parent = index.internalPointer().parent()
        return self.createIndex(parent.row(), 0, parent)
            
    def rowCount(self, parent):
        if not parent.isValid():
            return len(self._databases)
        else:
            return parent.internalPointer().childrenCount()
            
    def columnCount(self, parent):
        return 1
            
    def data(self, index, role):
        if index.isValid() and role in (Qt.DisplayRole, Qt.DecorationRole):
            if role == Qt.DisplayRole:
                return index.internalPointer().name()
            if role == Qt.DecorationRole:
                return QIcon('icons/database.png')
        return None


class MainWidget(QWidget):
    
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setLayout(QHBoxLayout())

        view = QTreeView()
        view.header().hide()
        view.setExpandsOnDoubleClick(False)
        self.model = FathomModel()
        view.setModel(self.model)
        
        self.display = QClickableTabWidget()

        self.layout().addWidget(view)
        self.layout().addWidget(self.display)
        
        self.connect(view, SIGNAL('doubleClicked(const QModelIndex &)'),
                     self.openElement)
                     
    def openElement(self, index):
        self.display.addTab(index.internalPointer().createWidget(),
                            index.internalPointer().name())
        
    def addDatabase(self, db):
        self.model.addDatabase(db)


class MainWindow(QMainWindow):
    
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent=parent)
        self.setWindowIcon(QIcon('icons/database.png'))
        self.setWindowTitle('QFathom')
        
        self.widget = MainWidget()
        self.setCentralWidget(self.widget)
        menu = self.menuBar().addMenu(self.tr('Connection'))

        action = QAction(QIcon('icons/add_database.png'), 
                         self.tr('Add &new..'), self)
        action.setIconVisibleInMenu(True)
        self.connect(action, SIGNAL('triggered()'), self.addConnection)
        menu.addAction(action)
        
        toolBar = QToolBar()
        toolBar.addAction(action)
        self.addToolBar(toolBar)
        
    def addConnection(self):
        dialog = QConnectionDialog()
        if dialog.exec() == QDialog.Accepted:
            params = dialog.getDatabaseParams()
            db = self.connectDatabase(params)
            self.widget.addDatabase(db)
            
    def connectDatabase(self, params):
        function = TYPE_TO_FUNCTION[params[0]]
        return function(*params[1:])


if __name__ == "__main__":
    app = QApplication(argv)
    window = MainWindow()
    window.show()
    app.exec()
