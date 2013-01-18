#encoding: utf8
"""
when doing Fourier Transform, all default origin of result matrix are (M/2, N/2)
"""

import numpy as np, Image
from math import *

def change_origin(mat):
    """
    f(x,y) = f(x,y) * (-1)**(x + y)
    """
    w, h = mat.shape
    for x in xrange(w):
        for y in xrange(h):
            mat[x, y] *= (-1)**(x + y)
    
def img_from_array(array):
    """
    create gray image from array.
    """
    if array.dtype == np.uint8:
        return Image.fromarray( array )
    
    min, max = array.min(), array.max()
    factor = 1.0 / (max - min) * 255
    array = (array - min) * factor
    img = Image.fromarray( np.uint8(array) )
    return img

def fft_from_array(array):
    """
    get the result of Fourier transform.
    I have changed the origin to the center of fourier matrix.
    """
    change_origin(array)
    fft = np.fft.fft2( array )
    return fft

def split_fft(fft):
    """
    split fft matrix into two parts, one is phase matrix, the other
    one is frequence matrix
    """
    x, y = fft.shape
    phase = np.zeros((x, y))
    freq = np.zeros((x, y))
    for i in xrange(x):
        for j in xrange(y):
            freq[i, j] = sqrt(fft[i, j].real**2 + fft[i, j].imag**2)
            phase[i, j] = fft / freq[i, j]
    return phase, freq


#three low-pass filter
def BLPF(x, y, d0, n=1):
    """
    Potter Voss low-pass filter
    """
    h = np.zeros((x, y))
    for i in xrange(x):
        for j in xrange(y):
            d = sqrt( (i - x/2)**2 + (j - y/2)**2 )
            h[i, j] = 1.0 / (1 + (d/d0)**(2*n))
    return h

def ILPF(x, y, d0, n=0):
    """
    Ideal low-pass fiter
    """
    h = np.ones((x, y))
    d2 = d0 * d0
    for i in xrange(x):
        for j in xrange(y):
            if (i - x/2)**2 + (j - y/2)**2 > d2:
                h[i, j] = 0
    return h

def GLPF(x, y, d0, n=0):
    """
    Gaussian low-pass filter
    """
    h = np.zeros((x, y))
    dd = d0**2
    for i in xrange(x):
        for j in xrange(y):
            d2 = (i - x/2)**2 + (j - y/2)**2
            h[i, j] = np.exp( -0.5*d2/dd )
    return h


def low_filter_helper(img, func, d0, n=1):
    array = np.array(img)
    fft = fft_from_array(array)
    x, y = fft.shape

    r = np.fft.ifft2( fft * func(x, y, d0, n) ).real
    change_origin(r)
    img = img_from_array(r)
    return img

def do_ILPF_filter(img, d0=10):
    return low_filter_helper(img, ILPF, d0)

def do_BLPF_filter(img, d0, n=1):
    return low_filter_helper(img ,BLPF, d0, n)

def do_GLPF_filter(img, d0):
    return low_filter_helper(img, GLPF, d0)

from optparse import OptionParser

if __name__ == "__main__":
    parser = OptionParser("Usage: %prog [options] arg")
    parser.add_option("-o", "--output", dest="output", default="out",
                      help="specify the filename of output image.")
                
    options, arg = parser.parse_args()
    img = Image.open( arg[0] )

    #filter
    new_img = do_BLPF_filter(img, 10)

    output = "%s.png" % options.output
    new_img.save(output)
    print "%s saved" % output

