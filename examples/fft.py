from pixell import enmap, utils as u
import time
import numpy as np

shape,wcs = enmap.fullsky_geometry(res=2.0*u.arcmin)
imap = enmap.ones(shape,wcs)

def compute():
    a = enmap.fft(imap)

if __name__ == "__main__":
    start = time.perf_counter()
    compute()
    end = time.perf_counter()
    print(end - start)
    
