import threading

AUDIOSUPPORT = True
try:
    import simpleaudio as sa
except ModuleNotFoundError:
    AUDIOSUPPORT = False

class ElevatorPlayer(threading.Thread):
    def __init__(self, threadID, name, audiofile):
        super().__init__()
        self.threadID = threadID
        self.name = name
        self.audiofile = audiofile
        self.wobj = sa.WaveObject.from_wave_file(self.audiofile)
        self.doplay = True
    
    def run(self):
        print("plaing")
        while self.doplay:
            self.pobj = self.wobj.play()
            self.pobj.wait_done()
    
    def stop(self):
        print("stop")
        if hasattr(self, "pobj"):
            self.doplay = False
            self.pobj.stop()
           
    def is_playing(self):
        if hasattr(self, "pobj"):
            return self.pobj.is_playing()
