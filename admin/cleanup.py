#!/bin/env python
# Prepare a list of programs without examples for removing them from the stable version
from __future__ import print_function
import os
import rsf.doc
import rsf.prog

progs = rsf.doc.progs
for prog in list(progs.keys()):
    sfprog = rsf.doc.progs[prog]
    if not sfprog.uses:
        if not os.path.dirname(sfprog.file) in \
          ('system/main','plot/test','plot/main','plot/lib','su/plot','pens/main','user/ivlad','user/jennings','user/slim','user/godwinj'):
            print(sfprog.file)

