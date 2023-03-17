from PyMca5.PyMcaPhysics.xrf import FastXRFLinearFit
from XRDXRFutils.data import DataXRF, SyntheticDataXRF
import h5py
from os.path import basename, dirname, join, exists
from os import remove

class FastFit():
    def __init__(self, data = None, cfgfile = None, outputdir = None):
        self.data = data
        self.cfgfile = cfgfile
        self.outputdir = outputdir
        self.outputRoot = "IMAGES"
        if self.outputdir:
            self.filename = join(self.outputdir, f'{self.outputRoot}.h5')
        
    def fit(self):
        if type(self.data) != type(None) and self.cfgfile and self.outputdir:
            self.fastfit = FastXRFLinearFit.FastXRFLinearFit()
            self.fastfit.setFitConfigurationFile(self.cfgfile)

            outbuffer = self.fastfit.fitMultipleSpectra(
                y = self.data,
                weight = 1,
                refit = 1,
                concentrations = 0,
                outputDir = self.outputdir,
                outputRoot= self.outputRoot,
                h5  = True)

            zero = outbuffer['configuration']['detector']['zero']
            gain = outbuffer['configuration']['detector']['gain']
            self.parameters = (0, gain, zero)

            self._load_fit_results()
        
        return self

    def _load_fit_results(self):
        self.labels  = {}
        with h5py.File(self.filename, 'r') as f:
            keys = f['images']['xrf_fit']['results']['parameters'].keys()
            for k in keys:
                if 'errors' not in k:
                    label = f['images']['xrf_fit']['results']['parameters'][k][()]
                    self.labels[k.replace('_','-')] = label


    def get_labels(self):
        if hasattr(self, "labels"):
            return self.labels

    def get_calibration_pars(self):
        if hasattr(self, "parameters"):
            return self.parameters

        
