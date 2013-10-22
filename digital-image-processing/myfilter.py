import ImageChops, Image, ImageMath, ImageFilter
import numpy as np
from utils import *

class SOBEL(ImageFilter.Filter):
    name = "sobel filter"

    def filter(self, image):
        if image.mode != "L":
            raise ValueError("image mode must be L")
        dx = (3, 3), 1, 0, [-1, 0, 1, -2, 0, 2, -1, 0, 1]
        dy = (3, 3), 1, 0, [1, 2, 1, 0, 0, 0, -1, -2, -1]
        imx = Image.Image()._new(apply(image.filter, dx)) 
        imy = Image.Image()._new(apply(image.filter, dy))

        imx = imx.point(lambda i: abs(i), None)
        imy = imy.point(lambda i: abs(i), None)
        im = ImageChops.add(imx, imy)
        return im.im

def nonmax_supression(image, size=3):
    maxim = image.filter(ImageFilter.MaxFilter(size))
    maxim_array = np.array(maxim, dtype=np.uint32)
    image_array = np.array(image, dtype=np.uint32)
    try:
        div = (image_array+1) / (maxim_array+1) * image_array
    except:
        raise ZeroDivisionError("modulo by zero")
    return Image.fromarray( np.uint8(div) )

def canny_edge_detection(image, nonmaxsize=3):
    #gaussian smooth
    ga = np.array([2, 4, 5, 4, 2,
                   4, 9, 12, 9, 4,
                   5, 12, 15, 12, 5,
                   4, 9, 12, 9, 4,
                   2, 4, 5, 4, 2])
    ga = 1.0 / 159 * ga
    dga = (5, 5), ga, 1, 0
    image = image.filter(ImageFilter.Kernel(*dga))

    #sobel edge
    dx = (3, 3), [-1, 0, 1, -2, 0, 2, -1, 0, 1], 1, 0
    dy = (3, 3), [1, 2, 1, 0, 0, 0, -1, -2, -1], 1, 0
    imx = image.filter(ImageFilter.Kernel(*dx))
    imy = image.filter(ImageFilter.Kernel(*dy))

    imx = imx.point(lambda i: abs(i))
    imy = imy.point(lambda i: abs(i))
    im = ImageChops.add(imx, imy, 2)

    sizex, sizey = im.size
    
    mx = imx.load()
    my = imy.load()
    #edge direction
    theta = np.zeros((sizex, sizey))
    
    for i in xrange(sizex):
        for j in xrange(sizey):
            if mx[i, j] == 0:
                if my[i, j] == 0:
                    v = 0
                else:
                    v = 90.0
            else:
                v = np.degrees( np.arctan( my[i, j] / mx[i, j]) )

            if 22.5 >= v >= 0 or  180 >= v >=157.5:
                v = 0.0
            elif 67.5 >= v >= 22.5:
                v = 45.0
            elif 112.5 >= v >= 67.5:
                v = 90.0
            else:
                v = 135.0
            theta[i, j] = v
    #nonmax supression
    out = nonmax_supression(im, nonmaxsize)
    return out

if __name__== "__main__":
    x = Image.open("lena512.bmp")
    x = x.convert("L")
    
    canny = canny_edge_detection(x, 3)
    
    canny.save("lena_canny.png")
