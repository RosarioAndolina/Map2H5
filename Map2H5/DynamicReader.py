import threading
import io
import re
from glob import glob
from os.path import join, basename, exists
from os.path import split as pathsplit
from os import remove
from numpy import frombuffer, flip, zeros, asarray, uint16, where
from time import sleep
from Map2H5.FastFit import FastFit
from XRDXRFutils import DataXRF

class DynamicReader():
    def __init__(self, master, path, ndetector = 2):
        self.master = master
        self.path = path
        self.ndetector = ndetector
        head, tail = pathsplit(self.path)
        self.dpath = [join(self.path, tail + f'_{i}') for i in range(1, self.ndetector + 1)]
        self.queue = [list() for i in range(self.ndetector)]
        self.queuelock = [threading.Lock() for i in range(self.ndetector)]
        self.fitlock = threading.Lock()
        self.get_scanning_par()
        self.observer = [Observer(f'observer{i+1}', self.dpath[i], self.queue[i], self.queuelock[i]) for i in range(self.ndetector)]
        self.reader = [Reader(f'reader{i+1}',self.master, self.queue[i], self.queuelock[i], self.fitlock, self.rowlen, self.nrow) for i in range(self.ndetector)]
        #print(f"dynamicReader: {len(self.observer)} observers {len(self.reader)} readers {self.ndetector} detectors")
    
    def get_scanning_par(self):
        with open(join(self.path, "Scanning_Parameters.txt")) as f:
            lines = []
            for i in range(4):
                lines += [f.readline()]
        self.rowlen = int(re.findall(r'[0-9]+', lines[0])[-1])
        self.nrow = int(re.findall(r'[0-9]+', lines[2])[-1])
        return self
        
    def start_reading(self):
        for i in range(self.ndetector):
            self.observer[i].start()
            self.reader[i].start()
    
    def stop_reading(self):
        for i in range(self.ndetector):
            self.reader[i].read = False
            self.observer[i].whatch = False
            self.observer[i].join()
        
            #while self.queue[i]:
            #    self.reader[i].process_file(self.queue[i].pop(0))
            self.reader[i].finalize()
            
            self.reader[i].join()
        
        
class Observer(threading.Thread):
    def __init__(self, name, path, queue, lock):
        super().__init__()
        self.name = name
        self.path = path
        self.queue = queue
        self.lock = lock
        self.filelist = []
        self.whatch = True
        #print(f"{self.name} observing")
    
    def run(self):
        while self.whatch:
            newfilelist = sorted(glob(join(self.path, "*.map")))
            newfiles = [x for x in newfilelist if x not in self.filelist]
            if len(newfiles) != 0:
                self.lock.acquire()
                self.queue += newfiles
                self.lock.release()
                self.filelist = newfilelist
            sleep(0.1)

class Reader(threading.Thread):
    def __init__(self, name, master, queue, queuelock, fitlock, *scanning_par):
        super().__init__()
        self.name = name
        self.master = master
        self.queue = queue
        self.queuelock = queuelock
        self.fitlock = fitlock
        self.read = True
        self.ftoread = None
        self.rowlen, self.nrow = scanning_par
        self.channels = 2048
        #print(f'{self.name} on')

        
    def run(self):
        while self.read:
            self.queuelock.acquire()
            if len(self.queue) >= 2:
                self.ftoread = self.queue.pop(0)
            self.queuelock.release()
            if self.ftoread: self.process_file()
            self.ftoread = None
            sleep(0.1)

    @staticmethod
    def read_map(filename, shape = (-1,2048), rowlen = None, n = None):
        buffer = io.BytesIO()
        nchannels = shape[1]
        with open(filename, 'rb') as f:
            buffer.write(f.read())

        bl = len(buffer.getbuffer())
        hlen = bl%2048

        buffer.seek(hlen*2)
        x = frombuffer(buffer.read(), uint16)

        x = x.byteswap()

        size_idx = where(((x % nchannels) == 0) & (x>0))[0]

        newx = []
        for i in size_idx:
            for j in range(x[i]//nchannels):
                a = i+1+(nchannels)*j
                b = a+nchannels
                newx += [x[a:b]]
        
        if len(newx) > rowlen: newx = newx[:rowlen]
        if n%2 == 0:
            newx = asarray(newx + [zeros(nchannels)]*(rowlen-len(newx)))
        else:
            newx = asarray([zeros(nchannels)]*(rowlen-len(newx)) + newx)

        newx = newx.reshape(*shape)

        return newx


    def process_file(self, _file = None):
        if not _file: _file = self.ftoread
        #print(f'{self.name}: reading {_file}')
        n = int(re.findall(r"[0-9]+", basename(_file).split("Row")[1])[0])
        x = self.read_map(_file, shape = (-1, self.channels), rowlen = self.rowlen, n = n)
        if n%2 == 0:
            x = flip(x)
        self.fitlock.acquire()
        ffit = FastFit(data = x, cfgfile = self.master.cfgfile, outputdir = self.master.outputdir)
        if exists(ffit.filename): remove(ffit.filename)
        ffit.fit()
        #l = ffit.get_labels()
        remove(ffit.filename)
        for i,(k,v) in enumerate(ffit.get_labels().items()):
            self.master.labels[k][n] += v
        self.master.data.data[n] += x
        self.master.update_imarray()
        self.fitlock.release()

    def finalize(self):
        while self.queue:
            self.process_file(_file = self.queue.pop(0))
        
