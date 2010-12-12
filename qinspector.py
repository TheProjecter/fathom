#!/usr/bin/python

from sys import argv

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


class QVerticalWidget(QWidget):
    
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        self.setLayout(QVBoxLayout())
        
        
class QHorizontalWidget(QWidget):
    
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        self.setLayout(QHBoxLayout())


class QOkCancelWidget(QWidget):

        def __init__(self, okFunction=None, cancelFunction=None, parent=None):
                QWidget.__init__(self, parent)
                self.setLayout(QHBoxLayout())
                self.__ok = QPushButton('Ok')
                self.__cancel = QPushButton('Cancel')
                self.layout().addStretch()
                self.layout().addWidget(self.__ok)
                self.layout().addWidget(self.__cancel)
                
                self.connect(self.__ok, SIGNAL('pressed()'), self.okPressed)
                if okFunction is not None:
                        self.connect(self.__ok, SIGNAL('pressed()'), okFunction)
                self.connect(self.__cancel, SIGNAL('pressed()'), self.cancelPressed)
                if cancelFunction is not None:
                        self.connect(self.__cancel, SIGNAL('pressed()'), cancelFunction)
                
        def ok(self):
                return self.__ok
                
        def cancel(self):
                return self.__cancel
                
        def okPressed(self):
                self.emit(SIGNAL('okPressed'))

        def cancelPressed(self):
                self.emit(SIGNAL('cancelPressed'))

        def setDefault(self, value):
                self.__ok.setDefault(value)
                self.__cancel.setDefault(value)         

        def setAutoDefault(self, value):
                self.__ok.setAutoDefault(value)
                self.__cancel.setAutoDefault(value)  


class QConnectionDialog(QDialog):
    
    '''
    Dialog for gathering information for connecting to the database.
    '''
    
    class PostgresWidget(QVerticalWidget):
        
        PARAMS = (("Host:", "host"), ("Port:", "port"),
                  ("Database name:", "databaseName"), 
                  ("User name:", "userName"), ("Password:", "password")) 
        
        def __init__(self, parent=None):
            QVerticalWidget.__init__(self, parent)
            grid = QGridLayout()
            self.layout().addLayout(grid)
            self.layout().addStretch()
            
            for index, (label, field) in enumerate(self.PARAMS):
                label = QLabel(self.tr(label))
                grid.addWidget(label, index, 0, Qt.AlignLeft | Qt.AlignTop)            
                setattr(self, field, QLineEdit())
                grid.addWidget(getattr(self, field), index, 1)
                
        def validate(self):
            return bool(self.databaseName.text())
                
        def getDatabaseString(self):
            result = []
            for label, field in (('dbname', self.databaseName),
                                 ('user', self.userName)):
                if field.text():
                    result.append('%s=%s' % label, field.text())
            return ' '.join(result)


    class SqliteWidget(QVerticalWidget):
        
        def __init__(self, parent=None):
            QVerticalWidget.__init__(self, parent)
            model = QFileSystemModel()
            model.setRootPath(QDir.currentPath())
            index = model.index('/')
            view = QTreeView(parent=self);
            view.setModel(model)
            for i in range(1, 4):
                view.header().hideSection(i)
            self.layout().addWidget(view)
            
        def validate(self):
            False
            
        def getDatabaseString(self):
            pass

    
    def __init__(self, parent=None):
        QDialog.__init__(self)
        self.setLayout(QVBoxLayout())
        
        layout = QHBoxLayout()
        radioLayout = QVBoxLayout()
        
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
        layout.addLayout(radioLayout)

        self.currentWidget = None
        self.postgres.toggle()
        
        self.stackedWidget = QStackedWidget()
        self.stackedWidget.addWidget(self.PostgresWidget())
        self.stackedWidget.addWidget(self.SqliteWidget())
        layout.addWidget(self.stackedWidget)
        self.resize(600, 300)        
        self.layout().addLayout(layout)
        okCancel = QOkCancelWidget(okFunction=self.accept, 
                                   cancelFunction=self.reject)
        self.layout().addWidget(okCancel)

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

if __name__ == "__main__":
    main()

