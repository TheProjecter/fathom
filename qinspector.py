#!/usr/bin/python

from sys import argv
from os.path import join

from PyQt4.QtCore import (SIGNAL, QSettings, QDir, Qt, QVariant, QPoint, QSize)
from PyQt4.QtGui import (QWidget, QMainWindow, QApplication, QDialog, QAction, 
                         QRadioButton, QVBoxLayout, QHBoxLayout, QLineEdit,
                         QGridLayout, QLabel, QFileSystemModel, QTreeView,
                         QStackedWidget, QSizePolicy, QPushButton)

class WithSettings:

    def __init__(self, company, product):
        self.__company = company
        self.__product = product
        self.readSettings()

    def closeEvent(self, event):
        self.writeSettings()

    def readSettings(self):
        settings = QSettings(self.__company, self.__product)
        self.move(settings.value("position", QVariant(QPoint(200, 200))).toPoint())
        self.resize(settings.value("size", QVariant(QSize(400, 400))).toSize())
            
    def writeSettings(self):
        settings = QSettings(self.__company, self.__product)
        settings.setValue("position", QVariant(self.pos()))
        settings.setValue("size", QVariant(self.size()))


class QConnectionDialog(QDialog):
    
    '''
    Dialog for gathering information for connecting to the database.
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
                
        def getDatabaseString(self):
            result = []
            for label, field in (('dbname', self.databaseName),
                                 ('user', self.userName)):
                if field.text():
                    result.append('%s=%s' % label, field.text())
            return ' '.join(result)


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
            
        def getDatabaseString(self):
            index = self.view.currentIndex()
            result = []
            while index.isValid():
                result.append(unicode(index.data().toString()))
                index = index.parent()
            result.reverse()
            return join(*result)
    
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
        self.oracle.setDisabled(True)
        self.mysql.setDisabled(True)
        radioLayout.addStretch()
        self.postgres.toggle()
        
        # preparing stack widgets for database connection details
        self.stackedWidget = QStackedWidget()
        self.stackedWidget.addWidget(self.PostgresWidget())
        self.stackedWidget.addWidget(self.SqliteWidget())
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
            
    def getConnectionString(self):
        return self.stackedWidget.currentWidget().getDatabaseString()


class MainWindow(QMainWindow, WithSettings):
    
    def __init__(self):
        QMainWindow.__init__(self)
        WithSettings.__init__(self, '', 'dbinspect')
        self.createMenus()
        
    def createMenus(self):
        menu = self.menuBar().addMenu(self.tr('Connection'))
        action = QAction(self.tr('&New..'), self)
        action.setShortcut('Ctrl+N')
        self.connect(action, SIGNAL('triggered()'), self.newConnection)
        menu.addAction(action)
        
    def newConnection(self):
        dialog = QConnectionDialog()
        dialog.exec_()


def main():
    app = QApplication(argv)
    # window = MainWindow()
    # window.show()
    dialog = QConnectionDialog()
    dialog.show()
    app.exec_()
    print dialog.getConnectionString()

if __name__ == "__main__":
    main()
