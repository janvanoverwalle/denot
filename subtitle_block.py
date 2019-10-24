class SubtitleBlock(object):
    def __init__(self, index=-1):
        self._index = int(index)
        self._start_time = None
        self._end_time = None
        self._lines = []

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value):
        self._index = int(value)

    @property
    def start_time(self):
        return self._start_time

    @start_time.setter
    def start_time(self, value):
        self._start_time = str(value).strip()

    @property
    def end_time(self):
        return self._end_time

    @end_time.setter
    def end_time(self, value):
        self._end_time = str(value).strip()

    @property
    def timeframe(self):
        return self.start_time, self.end_time

    @timeframe.setter
    def timeframe(self, value):
        times = str(value).strip().split('-->')
        self._start_time = times[0].strip()
        self._end_time = times[1].strip()

    @property
    def lines(self):
        return self._lines

    @lines.setter
    def lines(self, value):
        self._lines = value if isinstance(value, list) else [value]

    def add_line(self, line):
        s_line = line.strip()
        if s_line:
            self._lines.append(s_line)

    def is_valid(self):
        return self.timeframe and self.lines

    def __str__(self):
        return '\n'.join([
            str(self.index),
            ' --> '.join(self.timeframe)
        ] + self.lines + ['\n'])
