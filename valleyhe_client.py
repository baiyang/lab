#!/usr/bin/python
#coding: utf-8

import xmlrpclib

proxy = xmlrpclib.ServerProxy("http://localhost:8080/")

def do( txt ):
    global proxy
    return proxy.do_text_segmentation( txt )

