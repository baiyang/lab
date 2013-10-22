from distutils.core import setup, Extension

ext = Extension("sum", sources = ['sum.cpp'])

setup (name = 'MySum',
       version = '1.0',
       description = "My own sum function",
       ext_modules = [ext])
