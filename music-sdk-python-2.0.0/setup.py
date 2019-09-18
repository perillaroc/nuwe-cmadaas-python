'''
Created on 2014/10/20

@author: sheva.wen
'''
from distutils.core import setup
import os

def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == "":
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)
 
 
packages = []
setup (
       name = 'music-sdk-python',
       version = '2.0.0',
       packages = ["cma","cma.music"],
       author = 'music api dev team',
       description = 'music api for python',
)