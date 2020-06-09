#!/usr/bin/env python

from timeit import timeit
import matplotlib

matplotlib.use('module://matplotlib-sixel')

from pylab import *

plot([1, 2, 3])
number = 1
time = timeit(lambda: show(), number=number)
time /= number
print(f"{time:.2f} seconds")
