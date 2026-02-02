# -*- coding: utf-8 -*-
from PyQt5.QtCore import QObject, QRunnable, pyqtSignal


class TaskSignals(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)


class TaskWorker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = TaskSignals()

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as exc:
            self.signals.error.emit(str(exc))
            return
        self.signals.finished.emit(result)
