#!/usr/bin/python
#-*- coding: utf-8 -*-

import re
from metarProcessing import metarProcessing

# step 1. Open file, and read it.
mp = metarProcessing('CYOW-2017-01.txt')
# mp.init('test.txt')

# step 1: read a record
res = mp.getNextRecord()
resList = mp.getMetarList(res)

# step 2: decode

# res2 = mp.getNextRecord()
