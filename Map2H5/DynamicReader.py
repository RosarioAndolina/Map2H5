import multiprocessing
from queue import Queue
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
    def __init__(self, root, path, ndetector = 2):
        self.root = root
        self.path = path
        self.ndetector = ndetector
        head, tail = pathsplit(self.path)
        self.dpath = [join(self.path, tail + f'_{i}') for i in range(1, self.ndetector + 1)]
        self.queue = [Queue() for i in range(self.ndetector)]
        self.queuelock = [multiprocessing.Lock() for i in range(self.ndetector)]
        self.fitlock = multiprocessing.Lock()
        self.get_scanning_par()
        self.observer = [Observer(self, i+1 ,f'observer{i+1}', self.dpath[i]) for i in range(self.ndetector)]
        self.reader = [Reader(self.root, self, i+1, f'reader{i+1}', self.rowlen, self.nrow) for i in range(self.ndetector)]
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
        
        
class Observer(multiprocessing.Process):
    def __init__(self, master, threadId,  name, path):
        super().__init__()
        self.master = master
        self.threadId = threadId
        self.name = name
        self.path = path
        self.queue = self.master.queue[self.threadId - 1]
        self.lock = self.master.queuelock[self.threadId - 1]
        self.filelist = []
        self.whatch = True
    
    def run(self):
        while self.whatch:
            newfilelist = sorted(glob(join(self.path, "*.map")))
            newfiles = [x for x in newfilelist if x not in self.filelist]
            if len(newfiles) != 0:
                self.lock.acquire()
                try:
                    for nf in newfiles:
                        self.queue.put(nf)
                finally:
                    self.lock.release()
                self.filelist = newfilelist
            sleep(0.1)

class Reader(multiprocessing.Process):
    def __init__(self, root, master, threadId, name, *scanning_par):
        super().__init__()
        self.root = root
        self.master = master
        self.threadId = threadId
        self.name = name
        self.queue = self.master.queue[self.threadId - 1]
        self.queuelock = self.master.queuelock[self.threadId - 1]
        self.fitlock = self.master.fitlock
        self.read = True
        self.ftoread = None
        self.rowlen, self.nrow = scanning_par
        self.channels = 2048
        #print(f'{self.name} on')

        
    def run(self):
        print(f'{self.name} queue lenght {self.queue.qsize()}')
        while self.read:
            self.queuelock.acquire()
            try:
                if self.queue.qsize() >= 2:
                    self.ftoread = self.queue.get()
                    print(f'{self.name} reading queuelen {self.queue.qsize()}')
            finally:
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
        try:
            ffit = FastFit(data = x, cfgfile = self.master.cfgfile, outputdir = self.master.outputdir)
            if exists(ffit.filename): remove(ffit.filename)
            ffit.fit()
            #l = ffit.get_labels()
            remove(ffit.filename)
            for i,(k,v) in enumerate(ffit.get_labels().items()):
                self.root.labels[k][n] += v
            self.root.data.data[n] += x
            self.root.update_imarray()
        finally:
            self.fitlock.release()

    def finalize(self):
        while True:
            self.queuelock.aquire()
            try:
                if not self.queue.empty():
                    self.process_file(_file = self.queue.get())
                else:
                    break
            finally:
                self.queuelock.release()
                
        