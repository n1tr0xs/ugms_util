import sys
import requests
from collections.abc import Iterable

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, pyqtSlot, QThreadPool, QObject, QRunnable, pyqtSignal
from PyQt6.QtWidgets import *

def get_json(page: str, parameters: dict={}, server: str='http://10.55.1.30:8640') -> dict:
    url = f'{server}/{page}?'
    for k, v in parameters.items():
        url += f'{k}='
        url += ','.join(map(str, v)) if isinstance(v, Iterable) else str(v)
        url += '&'
##    print(url)
    return requests.get(url).json()

class MainWindow(QMainWindow):
    keyPressed = QtCore.pyqtSignal(int)
    
    def __init__(self):
        '''
        Creates main window.
        '''
        super().__init__()
        
        self.settings = QtCore.QSettings('n1tr0xs', 'sinop measurement view')
                        
        self.layout = QGridLayout()

        self.centralWidget = QWidget()
        self.centralWidget.setLayout(self.layout)
        self.setCentralWidget(self.centralWidget)

        self.setFont(QtGui.QFont('Times New Roman', 12))
        self.setWindowTitle('')

        self.table = QTableWidget()
        self.layout.addWidget(self.table)

        # get stations list
        stations = dict()
        for row in get_json('stations.json'):
            index, name = row['sindex'], row['station_name']
            if name.startswith('МС'):
                stations[index] = name
        
        names = [
            f'{name}, {index}'
            for index, name in sorted(
                stations.items(),
                key=lambda x: x[0]
            )
        ]
        self.table.setColumnCount(len(names))
        self.table.setHorizontalHeaderLabels(names)

        measurements = dict()
        resp = get_json('get', {'stations': stations.keys(), 'streams': 0})

        # vertical header labels
        bufr_name = dict()
        for station in stations:
            for row in get_json('station_taking.json', {'station': station}):
                bufr_name[row['code']] = row['caption']
        self.table.setRowCount(len(bufr_name))
        self.table.setVerticalHeaderLabels(f'{name}, {code}' for code, name in sorted(bufr_name.items(), key=lambda x: x[0]))

        
        
        
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        
        self.restore_settings()
        self.show()
##        self.setFixedSize(self.sizeHint())


    def closeEvent(self, event:QtGui.QCloseEvent):
        self.save_settings()
        super().closeEvent(event)
        
    def save_settings(self):
        '''
        Saves current window geometry.
        '''
        self.settings.setValue("geometry", self.saveGeometry())

    def restore_settings(self):
        '''
        Restores last window geometry.
        '''
        self.restoreGeometry(self.settings.value("geometry", type=QtCore.QByteArray))

    def keyPressEvent(self, event):
        '''
        Bindings in window.
        '''
        super().keyPressEvent(event)
        if event.key() == QtCore.Qt.Key.Key_Escape:
            self.close()
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    sys.exit(app.exec())
