from PyQt5.QtCore import QObject, pyqtSignal, QRunnable

class WorkerSignals(QObject):
    finished = pyqtSignal(object)  
    error = pyqtSignal(str)     

class TaskWorker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.finished.emit(result)
        except Exception as e:
            import traceback
            self.signals.error.emit(f"{e}\n{traceback.format_exc()}")