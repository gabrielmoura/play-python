#!/usr/bin/env python3.7

#from distutils.core import setup
#from distutils.extension import Extension
#from Cython.Distutils import build_ext
#from Cython.Build import cythonize

#ext_modules = [
#    Extension("srmoura_xmpp", ["bot_commander"]),
#]
#from setuptools import setup
import time
import os
from setuptools import setup
import compileall
setup(
    name='srmoura_xmpp',
    version=time.strftime('%Y.%m.%d.%H.%M.%S', time.gmtime(1520986859.625666)),
    description='SrMoura.',
    author='Gabriel Moura',
    author_email='develop@srmoura.com.br',
    license="Custom",
    long_description='SrMoura.',
    url='https://github.com/srmoura/Arch',
    py_modules=['bot_commander'],
    #package_dir={'': './'},
    install_requires=['sleekxmpp', 'dnspython'],
    include_package_data=True,

)
#setup_dir = os.path.dirname(os.path.realpath(__file__))+'/build/lib/'
#compileall.compile_dir(setup_dir,optimize=1)
#print(setup_dir)
