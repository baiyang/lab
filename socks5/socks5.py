from collections import namedtuple
from socket import *
import threading 
import select, struct

socks5 = socket(AF_INET, SOCK_STREAM, 0)

class Connection:
    def __init__(self, c, s, is_server):
        self.server = s
        self.client = c
        self.is_server = is_server

READ_THREAD = 3

wait_queue = []
ready_queue = []
read_queue = []

mutex_wait = threading.Lock()
mutex_read = threading.Lock()

cond_read = threading.Condition( mutex_read )

def do_select():
    global ready_queue
    while True:
        mutex_wait.acquire()
        ready_queue.extend( wait_queue )
        del wait_queue[:]
        mutex_wait.release()

        print "ready_queue: ", len(ready_queue)
        
        rlist = [conn.server for conn in ready_queue]
        rlist.extend( [conn.client for conn in ready_queue] )

        r, w, e = select.select(rlist, [], [], 1)
        if r:
            # check closed socket and sockets who read data
            remove_index = []
            read_index = []
            for i, conn in enumerate(ready_queue):
                try:
                    if conn.server in r:
                        conn.is_server = True
                        probe = conn.server.recv(1, MSG_PEEK)
                        if probe:
                            read_index.append( i )
                        else:
                            remove_index.append( i )
                    
                    if conn.client in r:
                        conn.is_server = False
                        probe = conn.client.recv(1, MSG_PEEK)
                        if probe:
                            read_index.append( i )
                        else:
                            remove_index.append( i )
                except timeout:
                    print "timeout"
                    pass
                except error, msg:
                    print msg
                    remove_index.append( i )
            # push into read_queue first
            cond_read.acquire()
            del read_queue[:]
            for i in read_index:
                read_queue.insert( 0, ready_queue[i] )
            if read_queue:
                cond_read.notify_all()
            cond_read.release()
            # delete all of closed connection
            next_index = []
            for i, conn in enumerate( ready_queue ):
                if i in remove_index:
                    conn.server.close()
                    conn.client.close()
                else:
                    next_index.append( i )
            ready_queue = [ready_queue[i] for i in next_index]
        else: # timeout
            continue 

def do_handle():
    while True:
        conn = None
        cond_read.acquire()
        while not conn:
            try:
                print "read queue:", len(read_queue)
                conn = read_queue.pop()
            except IndexError:
                cond_read.wait()
        cond_read.release()
        try:
           if conn.is_server:
               conn.client.send( conn.server.recv(4096) )
           else:
               data = conn.client.recv(4096)
               print data
               conn.server.send( data )
        except:
            pass

def do_confirm_request(client, addr):
    req = client.recv(512)

    if req[0] != "\x05":
        client.close()
        return None
    
    client.send("\x05\x00")
    req = client.recv(512)
    req_cp = [e for e in req] # to list
    
    req_cp[1] = "\x00"
    if req[1] != "\x01": # connect command
        req_cp[1] = "\x07"

    try:
        if req[3] == "\x03":
            domain = req[5: 5 + ord(req[4])]
            domain = gethostbyname( domain )
            port = struct.unpack(">H", req[5 + ord(req[4]):])
        elif req[3] == "\x01":
            domain = inet_ntoa( req[4: 8] )
            port = struct.unpack(">H", req[8:])
        else:
            req_cp[1] = "\x01"
        s = socket(AF_INET, SOCK_STREAM, 0)
        s.connect( (domain, port[0]) )
    except herror:
        req_cp[1] = "\x04"
    except error:
        req_cp[1] = "\x03"
    
    if req_cp[1] != "\x00":
        client.send( "".join(req_cp) )
        client.close()
        return None
    print domain, port[0]
    client.send( "".join(req_cp) )
    return s

def do_listen():
    socks5.bind(("127.0.0.1", 1998))
    socks5.listen(10)
    print "listen on port 1080....."
    while True:
        client, addr = socks5.accept()
        server = do_confirm_request(client, addr)
        if server:
            client.settimeout(1)
            server.settimeout(1)
            mutex_wait.acquire()
            wait_queue.append( Connection(server, client, 0) )
            mutex_wait.release()
        else:
            print "Connection failed."
            
if __name__ == "__main__":
    _t = []
    _t.append( threading.Thread( target =  do_listen  ) )
    _t.append( threading.Thread( target = do_select ) )
    for i in xrange(READ_THREAD):
        _t.append( threading.Thread( target = do_handle ) )
    for t in _t:
        t.daemon = True
        t.start()
    for t in _t:
        t.join()
    
    
        
    


















    



    
