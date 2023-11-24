import sys
import requests
import datetime as dt
from collections.abc import Iterable

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, pyqtSlot, QThreadPool, QObject, QRunnable, pyqtSignal
from PyQt6.QtWidgets import *

def get_json(page: str, parameters: dict={}, server: str='http://10.55.1.30:8640') -> list:
    url = f'{server}/{page}?'
    for k, v in parameters.items():
        url += f'{k}='
        url += ','.join(map(str, v)) if isinstance(v, Iterable) else str(v)
        url += '&'
    try:
        return requests.get(url).json()
    except requests.exceptions.JSONDecodeError:
        return list()
        

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.
    Supported signals are:
    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal()
    progress = pyqtSignal()


class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function
    '''
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        
        # Add the callback to our kwargs
        self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit()  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done

class MainWindow(QMainWindow):
    keyPressed = QtCore.pyqtSignal(int)
    
    def __init__(self):
        '''
        Creates main window.
        '''
        super().__init__()
        
        self.settings = QtCore.QSettings('n1tr0xs', 'sinop measurement view')
        self.threadpool = QThreadPool.globalInstance()
                        
        self.layout = QGridLayout()

        self.centralWidget = QWidget()
        self.centralWidget.setLayout(self.layout)
        self.setCentralWidget(self.centralWidget)

        self.setFont(QtGui.QFont('Times New Roman', 12))
        self.setWindowTitle('')

        self.label_term = QLabel('Срок:')
        self.layout.addWidget(self.label_term, 0, 0)

        self.term_box = QComboBox()
        self.layout.addWidget(self.term_box, 0, 1)

        self.label_last_update = QLabel('Последнее обновление:')
        self.layout.addWidget(self.label_last_update, 0, 2)
    
        self.table = QTableWidget()
        self.layout.addWidget(self.table, 1, 0, 1, 3)

        self.timer = QtCore.QTimer()
        self.timer.setInterval(10*1000)
        self.timer.timeout.connect(self.create_worker)
        self.timer.start()

        self.get_stations()
        self.get_terms()
        self.get_measurements_types()
        self.create_worker()
        
        self.restore_settings()
        self.show()

    def create_worker(self):
        '''
        Creates and starts worker for info update.
        '''
        worker = Worker(self.update_data)
        self.threadpool.start(worker)

    def get_stations(self):
        '''
        Gets station list.
        Sets vertical header labels.
        '''
        self.stations = dict()
        for row in get_json('stations.json'):
            index, name = row['sindex'], row['station_name']
            if name.startswith('МС'):
                self.stations[index] = name
        names = [
            f'{name} [{index}]'
            for index, name in sorted(
                self.stations.items(),
                key=lambda x: x[0]
            )
        ]
        self.table.setColumnCount(len(names))
        self.table.setHorizontalHeaderLabels(names)
        
    def get_terms(self):
        '''
        Gets available terms.
        Adds them into the `self.term_box`.
        '''
        resp = get_json('get', {'streams': 0, 'stations': self.stations.keys()})
        self.terms = sorted(filter(bool, set(row['point_at'] for row in resp)), reverse=True)
        for term in self.terms:
            self.term_box.addItem(f'{dt.datetime.utcfromtimestamp(term)} UTC')

    def get_measurements_types(self):
        '''
        Gets types of measurements.
        Sets vertical header labels.
        '''
        self.bufr_name = dict()
        for station in self.stations:
            for row in get_json('station_taking.json', {'station': station}):
                self.bufr_name[row['code']] = row['caption']
        vhl = [
            f'{name}'
            for code, name in sorted(
                self.bufr_name.items(),
                key=lambda x: x[0]
            )
        ]
        self.table.setRowCount(len(self.bufr_name))
        self.table.setVerticalHeaderLabels(vhl)

    def get_measurements(self):
        '''
        Gets measurements.
        '''
        self.meas_for_table = dict()
        for station in self.stations:
            resp = get_json('get', {'stations': station, 'streams': 0, 'point_at': point})
            for r in resp:
                bufr = r['code']
                station = r['station']
                value = r['value']
                unit = r['unit']
                if self.meas_for_table.get(bufr, None) is None:
                    self.meas_for_table[bufr] = dict()
                self.meas_for_table[bufr][station] = f'{value} {unit}'
                
    def update_table_data(self):
        '''
        Updates values of `self.table` items.
        '''
        for i, bufr in enumerate(sorted(self.bufr_name)):
            for j, station in enumerate(sorted(self.stations)):
                try:
                    item = QTableWidgetItem(self.meas_for_table[bufr][station])
                except KeyError:
                    item = QTableWidgetItem('-'*3)
                finally:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.table.setItem(i, j, item)
                    
    def update_data(self, *args, **kw):
        '''
        Gets info using REST API from server.
        Updates info in `self.table`.
        '''
        self.label_last_update.setText(f'Обновление, подождите...')

        point = self.terms[self.term_box.currentIndex()]

        get_measurements()
        update_table_data()
        
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.label_last_update.setText(f'Последнее обновление: {dt.datetime.now()}')
        
    def closeEvent(self, event:QtGui.QCloseEvent):
        self.save_settings()
        self.timer.stop()
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
