#!/bin/env python
# Make a list of main programs in the current directory 
from __future__ import print_function
import os, glob

mlist = []
for mfile in glob.glob('M*.c'):
    mlist.append(os.path.splitext(mfile)[0][1:])

mlist.sort()
print(' '.join(mlist))

