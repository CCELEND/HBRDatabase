# from distutils.core import setup
# from Cython.Build import cythonize

# setup(ext_modules = cythonize("get_ct.pyx"))


# setup.py
from distutils.core import setup, Extension
from Cython.Build import cythonize
import numpy
setup(ext_modules = cythonize(Extension(
    'get_ct',
    sources=['get_ct.pyx'],
    language='c',
    include_dirs=[numpy.get_include()],
    library_dirs=[],
    libraries=[],
    extra_compile_args=[],
    extra_link_args=[]
)))
