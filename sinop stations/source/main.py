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
        url += f'{k}='
        url += ','.join(map(str, v)) if isinstance(v, Iterable) else str(v)
        url += '&'
    return requests.get(url).json()

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.
    Supported signals are:

    finished
        No data
    error
        tuple (exctype, value, traceback.format_exc() )
    result
        object data returned from processing
    progress
        ImageQt to draw
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

        self.label_last_update = QLabel('Последнее обновление:')
        self.layout.addWidget(self.label_last_update, 0, 1)

        self.table = QTableWidget()
        self.layout.addWidget(self.table, 1, 0, 1, 2)

        self.timer = QtCore.QTimer()
        self.timer.setInterval(10*1000)
        self.timer.timeout.connect(self.start_update)
        self.timer.start()
        self.start_update()
        
        self.restore_settings()
        self.show()

    def start_update(self):
        '''
        '''
        worker = Worker(self.update_data)
        self.threadpool.start(worker)
    
    def update_data(self, *args, **kw):
        # get time and calculate last term
        time_step = dt.timedelta(hours=3)
        now = dt.datetime.utcnow()
        today = dt.datetime.utcnow().date()
        point = dt.datetime(today.year, today.month, today.day, 0, 0, 0)
        point += ((now-point) // time_step * time_step)
        
        self.label_term.setText(f'Срок: {point} UTC')
        self.label_last_update.setText(f'Обновление, подождите...')
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
        self.label_last_update.setText(f'Последнее обновление: {dt.datetime.now()}')
        
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
