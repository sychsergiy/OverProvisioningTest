import time


class TimerWrongUsageError(Exception):
    pass


class StartMethodNotCalledError(TimerWrongUsageError):
    def __str__(self):
        return "Start time has not been set, call start() method before."


class EndMethodNotCalledError(TimerWrongUsageError):
    def __str__(self):
        return "End time has not been set, call end() method before."


class Timer:
    """
    can be used as context manager, stops after exit from context manager:
        >>> with Timer() as t:
        >>>     pass
        >>>     print(t.elapsed)
        >>>     pass
        >>> print(t.elapsed)

    can be use as class:
        >>> timer = Timer()
        >>> timer.start()
        >>> timer.start_time
        >>> pass
        >>> timer.elapsed
        >>> timer.elapsed
        >>> timer.end()
        >>> timer.elapsed
        >>> timer.elapsed
    """

    def __init__(self):
        self._start_time = None
        self._end_time = None

    @staticmethod
    def _now():
        return time.time()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end()

    @property
    def elapsed(self) -> float:
        self._check_started()

        end_time = self._end_time if self._end_time else self._now()
        return end_time - self._start_time

    @property
    def start_time(self) -> float:
        self._check_started()
        return self._start_time

    @property
    def end_time(self) -> float:
        self._check_ended()
        return self._end_time

    def start(self):
        self._start_time = self._now()

    def end(self):
        self._end_time = self._now()

    def _check_started(self):
        if self._start_time is None:
            raise StartMethodNotCalledError()

    def _check_ended(self):
        if self._start_time is None:
            raise EndMethodNotCalledError()
