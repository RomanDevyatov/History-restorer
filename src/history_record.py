HISTORY_RECORD_DELEMITER = ", Visited On "


class HistoryRecord(object):
    url  = ""
    date = ""

    def __init__(self, url, date):
        self.url = url
        self.date = date

    def __repr__(self):
        return f"{self.url}{HISTORY_RECORD_DELEMITER}{self.date}"
    
    def __eq__(self, other):
        if not isinstance(other, type(self)): return NotImplemented
        return self.url == other.url
        
    def __hash__(self):
        return hash(self.url)
