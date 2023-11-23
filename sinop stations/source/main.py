import sys
import requests
import datetime as dt
from collections.abc import Iterable

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, pyqtSlot, QThreadPool, QObject, QRunnable, pyqtSignal
from PyQt6.QtWidgets import *

def get_json(page: str, parameters: dict={}, server: str='http://10.55.1.30:8640') -> dict:
    url = f'{server}/{page}?'
    for k, v in parameters.items():
        url += f'{k}=' + ','.join(map(str, v)) if isinstance(v, Iterable) else str(v) + '&'
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

        self.label = QLabel('Срок:')
        self.layout.addWidget(self.label, 0, 0)

        self.buttonUpdate = QPushButton('Обновить данные')
        self.buttonUpdate.clicked.connect(self.update_data)
        self.layout.addWidget(self.buttonUpdate, 0, 1)

        self.table = QTableWidget()
        self.layout.addWidget(self.table, 1, 0, 1, 2)

        self.update_data()
        self.restore_settings()
        self.show()

    def update_data(self):
        self.buttonUpdate.setText('Подождите...')
        self.buttonUpdate.setEnabled(False)
        # horizontal header labels
        stations = dict()
        for row in get_json('stations.json'):
            index, name = row['sindex'], row['station_name']
            if name.startswith('МС'):
                stations[index] = name
        
        names = [
            f'{name}'
            for index, name in sorted(
                stations.items(),
                key=lambda x: x[0]
            )
        ]
            
        self.table.setColumnCount(len(names))
        self.table.setHorizontalHeaderLabels(names)

        # vertical header labels
        bufr_name = dict()
        for station in stations:
            for row in get_json('station_taking.json', {'station': station}):
                bufr_name[row['code']] = row['caption']
        vhl = [
            f'{name}'
            for code, name in sorted(
                bufr_name.items(),
                key=lambda x: x[0]
            )
        ]
        self.table.setRowCount(len(bufr_name))
        self.table.setVerticalHeaderLabels(vhl)

        # measurements values
        time_step = dt.timedelta(hours=3)
        now = dt.datetime.utcnow()
        today = dt.datetime.utcnow().date()
        point = dt.datetime(today.year, today.month, today.day, 0, 0, 0)
        point += ((now-point) // time_step * time_step)
        self.label.setText(f'Срок: {point} UTC. Последнее обновление: {dt.datetime.now()}')
        meas_for_table = dict()
        for station in stations:
            resp = get_json('get', {'station': station, 'streams': 0, 'point_at': point.timestamp()})
            for r in resp:
                bufr = r['code']
                station = r['station']
                value = r['value']
                unit = r['unit']
                if meas_for_table.get(bufr, None) is None:
                    meas_for_table[bufr] = dict()
                meas_for_table[bufr][station] = f'{value} {unit}'

        # update data in QTableWidget
        for i, bufr in enumerate(sorted(bufr_name)):
            for j, station in enumerate(sorted(stations)):
                try:
                    self.table.setItem(i, j, QTableWidgetItem(meas_for_table[bufr][station]))
                except KeyError:
                    self.table.setItem(i, j, QTableWidgetItem('-'*3))

        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.buttonUpdate.setText('Обновить данные')
        self.buttonUpdate.setEnabled(True)
        
    
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
