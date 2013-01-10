from ctypes import *

class Point(Structure):
    """
    Specify the structure of point. Just use like Vertex buffer in openGL.
    """
    _fields_ = [("r", c_float),
                ("g", c_float),
                ("b", c_float),
                ("x", c_float),
                ("y", c_float),
                ("z", c_float)]

x = (Point * 10) ()

#convert to c_float array, you can get point buffer though these way.
y = cast(x, POINTER(c_float))
