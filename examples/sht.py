from pixell import enmap, curvedsky as cs, utils as u
import time
import numpy as np

shape,wcs = enmap.fullsky_geometry(res=2.0*u.arcmin)
imap = enmap.ones(shape,wcs)
lmax = 4000

def compute():
    a = cs.map2alm(imap,lmax=lmax)

if __name__ == "__main__":
    start = time.perf_counter()
    compute()
    end = time.perf_counter()
    print(end - start)
    
