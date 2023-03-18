#!/usr/bin/env python
from distutils.core import setup

setup(name='Map2H5',
    version='0.2',
    description='Read .map XRF data and write as HDF5',
    author='Rosario Andolina',
    author_email='andolinarosario@gmail.com',
    packages = ['Map2H5'],
    package_dir = {'Map2H5' : 'Map2H5'},
    install_requires = ["customtkinter", "pymca", "PyQt5", "Pillow"],
    data_files = [('share/Map2H5', ['Map2H5/elevator-music.wav'])],
    #    "XRDXRFutilst"],
    #dependency_links = ["", "git+ssh://git@github.com:zpreisler/XRDXRFutils.git"],
    scripts = ['Map2H5/map2h5','Map2H5/map2h5.bat','Map2H5/PyMcaAdvFit']
    )
