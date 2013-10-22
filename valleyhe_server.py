#!/usr/bin/python
#coding: utf-8

import xmlrpclib
from SimpleXMLRPCServer import SimpleXMLRPCServer
from smallseg import SEG
seg = SEG()

def do_text_segmentation(text):
    global seg
    text = text.encode( "utf-8" )
    wlist = seg.cut(text)
    wlist.reverse()
    result = []
    for i in wlist:
        if i:
            result.append( i )
    return  result  

seg_server = SimpleXMLRPCServer(("localhost", 8080))
seg_server.register_function(do_text_segmentation, "do_text_segmentation")
seg_server.serve_forever()
        

