"""
Note:
This file defines two c++-extension function.
The first one:
set_config(pts, nr, left_bottom, right_top, model_view, proj, viewport, stride, offset)

The second one:
idx_list = get_selected_index()
"""
import  ctypes  as t
import numpy

__all__ = ["build_array", "set_config", "get_selected_index"]

fullname = t.util.find_library("selection")
if not fullname:
    raise "selection.dll not found" 
selection = t.CDLL(fullname)

def build_array(ctype, v):
    try:
        x = (ctype * len(v))(*v)
    except:
        t = v.tolist()
        v = []
        for i in t:
            v += i
        x = (ctype * len(v))(*v)
    return x

def set_config(pts, nr, lb, rt, mv, proj, viewport, stride, offset):
    try:
        f_pts = build_array(t.c_float, pts)
        i_nr = t.c_int(nr)
        f_lb = build_array(t.c_float, lb)
        f_rt = build_array(t.c_float, rt)
        f_mv = build_array(t.c_float, mv)
        f_proj = build_array(t.c_float, proj)
        i_view = build_array(t.c_int, viewport)
        i_stride = t.c_int(stride)
        i_offset = t.c_int(offset)
        
        selection.set_config(f_pts, i_nr, f_lb, f_rt, f_mv, f_proj, i_view, i_stride, i_offset)
    except:
        pass

def get_selected_index():
    try:
        size = selection.get_selected_index_size()
        c_int_list = (t.c_int * size)()
        selection.get_selected_index(t.byref(c_int_list))
        return  list(c_int_list)
    except:
        raise "error in get_selected_index in %s.py file" % __name__
