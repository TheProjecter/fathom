#!/usr/bin/python3

from sys import argv
from os.path import join

from PyQt4.QtCore import (QDir, SIGNAL, Qt, QAbstractItemModel, QModelIndex,
                          QVariant, QCoreApplication, QEvent, QSettings, QPoint,
                          QSize)
from PyQt4.QtGui import (QDialog, QHBoxLayout, QWidget, QLabel, QStackedWidget,
                         QRadioButton, QLineEdit, QTreeView, QGridLayout,
                         QVBoxLayout, QPushButton, QFileSystemModel, QIcon,
                         QApplication, QTreeView, QMainWindow, QAction,
                         QTabWidget, QMenu, QToolBar, QTableWidget, QLineEdit,
                         QTableWidgetItem, QGroupBox, QGridLayout, QCursor)

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
            self.model.setRootPath('/')

            # preparing tree view displaying file system
            self.view = QTreeView(parent=self);
            self.view.setModel(self.model)
            for i in range(1, 4):
                self.view.header().hideSection(i)
            self.view.header().hide()

            # expanding tree view to show current working directory
            path = QDir.currentPath().split('/')
            fullPath = ''
            for step in path:
                fullPath += step + '/'
                index = self.model.index(fullPath)
                if index.isValid():
                    self.view.setExpanded(index, True)
                else:
                    break
            
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
        self.resize(600, 400)
        
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
        
        def removable(self):
            return False
    
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

        def removable(self):
            return True


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
            return TableDetailsWidget(self._table)

    def __init__(self, parent=None):
        QAbstractItemModel.__init__(self, parent)
        self._databases = []
        
    def addDatabase(self, database):
        count = len(self._databases)
        self.beginInsertRows(QModelIndex(), count, count + 1)
        self._databases.append(self.DatabaseItem(database, count))
        self.endInsertRows()
        
    def removeDatabase(self, database):
        index = self._databases.index(database)
        assert index > -1, 'Database to be removed not found!'
        self.beginRemoveRows(QModelIndex(), index, index + 1)
        self._databases.pop(index)
        self.endRemoveRows()
        
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
        layout = QVBoxLayout()

        # creating button for adding connections
        button = QPushButton(self.tr('Add connection..'))
        button.setIcon(QIcon('icons/add_database.png'))
        
        # creating view for displaying connections
        view = QTreeView()
        view.setFixedWidth(250)
        view.header().hide()
        view.setExpandsOnDoubleClick(False)
        self.model = FathomModel()
        view.setModel(self.model)
        
        # creating widget for displaying inspected objects
        self.display = QClickableTabWidget()

        # merging it all together
        layout.addWidget(button)
        layout.addWidget(view)
        self.layout().addLayout(layout)
        self.layout().addWidget(self.display)
        
        # connecting to signals
        self.connect(button, SIGNAL('pressed()'), self.addConnection)
        self.connect(view, SIGNAL('doubleClicked(const QModelIndex &)'),
                     self.openElement)
        self.connect(view, SIGNAL('pressed(const QModelIndex &)'),
                     self.editElement)
        
        # filling connections view with stored connections
        self.loadConnections()
                     
    def openElement(self, index=None):
        if index is None:
            index = self.sender().index
        self.display.addTab(index.internalPointer().createWidget(),
                            index.internalPointer().name())
                            
    def editElement(self, index):
        if QApplication.mouseButtons() == Qt.RightButton:
            menu = QMenu()
            action = QAction('Open', self)
            action.index = index
            self.connect(action, SIGNAL('triggered()'), self.openElement)
            menu.addAction(action)
            if index.internalPointer().removable():
                action = QAction('Remove', self)
                action.index = index
                self.connect(action, SIGNAL('triggered()'), self.removeElement)
                menu.addAction(action)
            menu.exec(QCursor.pos())
            
    def removeElement(self):
        index = self.sender().index
        self.model.removeDatabase(index.internalPointer())

    def loadConnections(self):
        settings = QSettings('gruszczy@gmail.com', 'qfathom')
        databases = settings.value('databases', [])
        for params in databases:
            try:
                db = self.connectDatabase(params)
            except FathomError:
                pass # warn at the end
            else:
                self.model.addDatabase(db)
        
    def addConnection(self):
        dialog = QConnectionDialog()
        if dialog.exec() == QDialog.Accepted:
            params = dialog.getDatabaseParams()
            try:
                db = self.connectDatabase(params)
            except FathomError as e:
                args = (self, 'Failed to connect to database',
                        'Failed to connect to database: %e' % str(e))
                QMessageBox.critical(*args)
            else:
                settings = QSettings('gruszczy@gmail.com', 'qfathom')
                databases = settings.value('databases', [])
                databases.append(params)
                settings.setValue('databases', databases)
                self.model.addDatabase(db)
            
    def connectDatabase(self, params):
        function = TYPE_TO_FUNCTION[params[0]]
        return function(*params[1:])


class MainWindow(QMainWindow):
    
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent=parent)
        self.setWindowIcon(QIcon('icons/database.png'))
        self.setWindowTitle('QFathom')
        self.setCentralWidget(MainWidget())

        settings = QSettings('gruszczy@gmail.com', 'qfathom')
        geometry = settings.value('main-window/geometry', None)
        if geometry is not None:
            self.restoreGeometry(geometry)

    def closeEvent(self, event):
        settings = QSettings("gruszczy@gmail.com", "qfathom")
        settings.setValue("main-window/geometry", self.saveGeometry())


class TableDetailsWidget(QWidget):
    
    def __init__(self, table, parent=None):
        QWidget.__init__(self, parent)
        self._table = table
        
        self.setLayout(QVBoxLayout())
        self.addTitle()
        self.addColumns()
        self.addForeignKeys()
        self.addIndices()
        self.layout().addStretch()

    def addTitle(self):
        label = QLabel('<h2>' + self._table.name + '</h2>')
        self.layout().addWidget(label)

    def addColumns(self):
        box = QGroupBox(self.tr('Columns'))
        layout = QGridLayout()
        layout.addWidget(QLabel(self.tr('<b>Name</b>')), 0, 0)
        layout.addWidget(QLabel(self.tr('<b>Type</b>')), 0, 1)
        layout.addWidget(QLabel(self.tr('<b>Not null</b>')), 0, 2)
        layout.addWidget(QLabel(self.tr('<b>Default</b>')), 0, 3)
        for index, column in enumerate(self._table.columns.values()):
            layout.addWidget(QLabel(column.name), index + 1, 0)
            layout.addWidget(QLabel(column.type), index + 1, 1)
            layout.addWidget(QLabel(str(column.not_null)), index + 1, 2)
            layout.addWidget(QLabel(column.default), index + 1, 3)
        box.setLayout(layout)
        self.layout().addWidget(box)
        
    def addForeignKeys(self):
        if self._table.foreign_keys:            
            box = QGroupBox(self.tr('Foreign keys'))
            layout = QGridLayout()
            layout.addWidget(QLabel(self.tr('<b>Columns</b>')), 0, 0)
            layout.addWidget(QLabel(self.tr('<b>Referenced table</b>')), 0, 1)
            layout.addWidget(QLabel(self.tr('<b>Referenced columns</b>')), 0, 2)
            for index, fk in enumerate(self._table.foreign_keys):
                layout.addWidget(QLabel(', '.join(fk.columns)), index + 1, 0)
                layout.addWidget(QLabel(fk.referenced_table), index + 1, 1)
                layout.addWidget(QLabel(', '.join(fk.referenced_columns)), 
                                        index + 1, 2)
            box.setLayout(layout)
            self.layout().addWidget(box)
        else:
            self.layout().addWidget(QLabel('No foreign keys defined.'))
            
    def addIndices(self):
        if self._table.indices:
            box = QGroupBox(self.tr('Indices'))
            layout = QGridLayout()
            layout.addWidget(QLabel(self.tr('<b>Name</b>')), 0, 0)
            layout.addWidget(QLabel(self.tr('<b>Columns</b>')), 0, 1)
            for index, table_index in enumerate(self._table.indices.values()):
                layout.addWidget(QLabel(table_index.name), index + 1, 0)
                layout.addWidget(QLabel(', '.join(table_index.columns)), 
                                 index + 1, 1)
            box.setLayout(layout)
            self.layout().addWidget(box)
        else:
            self.layout().addWidget(QLabel('No indices defined'))


if __name__ == "__main__":
    app = QApplication(argv)
    window = MainWindow()
    window.show()
    app.exec()
