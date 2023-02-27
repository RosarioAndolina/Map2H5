#!/usr/bin/env python
from distutils.core import setup

setup(name='Map2H5',
    version='0.1',
    description='Read .map XRF data and write as HDF5',
    author='Rosario Andolina',
    author_email='andolinarosario@gmail.com',
    install_requires = ["customtkinter"],
    #    "XRDXRFutilst"],
    #dependency_links = ["", "git+ssh://git@github.com:zpreisler/XRDXRFutils.git"],
    scripts = ['Map2H5/map2h5']
    )
