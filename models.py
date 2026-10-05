class Track:
    def __init__(self, filename, seconds, path):
        self.filename = filename
        self.seconds = seconds
        self.path = path

    def to_dict(self):
        return {"filename": self.filename, "seconds": self.seconds, "path": self.path}

