#!/usr/bin/python

from sys import argv
from PyQt4.QtCore import (SIGNAL, QSettings, QDir)
w
from PyQt4.QtGui import (QWidget, QMainWindow, QApplication, QDialog, QAction, 
                         QRadioButton, QVBoxLayout, QHBoxLayout, QLineEdit,
                         QGridLayout, QLabel, QFileSystemModel, QTreeView)


class QVerticalWidget(QWidget):
    
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        self.setLayout(QVBoxLayout())
        
        
class QHorizontalWidget(QWidget):
    
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        self.setLayout(QHBoxLayout())


class QConnectionDialog(QDialog):
    
    '''
    Dialog for gathering information for connecting to the database.
    '''
    
    class PostgresWidget(QWidget):
        
        def __init__(self, parent=None):
            QWidget.__init__(self, parent)
            self.setLayout(QGridLayout())
            self.fields = []
            
            self.layout().addWidget(QLabel(self.tr("Database name:")), 0, 0)
            self.databaseName = QLineEdit()
            self.layout().addWidget(self.databaseName, 0, 1)
            self.layout().addWidget(QLabel(self.tr("User name:")), 1, 0)
            self.userName = QLineEdit()
            self.layout().addWidget(self.userName, 1, 1)
            
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
            model = QFileSystemModel()
            model.setRootPath(QDir.currentPath())
            view = QTreeView(parent=self);
            view.setModel(model)

    
    def __init__(self, parent=None):
        QDialog.__init__(self)
        
        layout = QHBoxLayout()
        radioLayout = QVBoxLayout()
        
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
        
        layout.addLayout(radioLayout)
        self.setLayout(layout)

        self.currentWidget = None
        self.postgres.toggle()
        self.postgresChosen()

    def postgresChosen(self):
        if self.currentWidget is not None:
            self.currentWidget.setParent(None)
        self.currentWidget = self.PostgresWidget()
        self.layout().addWidget(self.currentWidget)
        
    def sqliteChosen(self):
        if self.currentWidget is not None:
            self.currentWidget.setParent(None)
        self.currentWidget.setParent(None)
        self.currentWidget = self.SqliteWidget()
        self.layout().addWidget(self.currentWidget)
    
    def oracleChosen(self):
        '''TODO: implement'''
        
    def mysqlChosen(self):
        '''TODO: implement'''


class MainWindow(QMainWindow):
    
    def __init__(self):
        QMainWindow.__init__(self)
        self.createMenus()
        
    def createMenus(self):
        menu = self.menuBar().addMenu(self.tr('Connection'))
        action = QAction(self.tr('&New..'), self)
        self.connect(action, SIGNAL('triggered()'), self.newConnection)
        menu.addAction(action)
        
    def newConnection(self):
        dialog = QConnectionDialog()
        dialog.exec_()


def main():
    app = QApplication(argv)
    window = MainWindow()
    window.show()
    app.exec_()

if __name__ == "__main__":
    main()

