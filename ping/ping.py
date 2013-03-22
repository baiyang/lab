#!/usr/bin/python
#date 2013/3//15
#author valleyhe


import os, socket, time, random
import sys, struct, select, threading

PING_COUNT, TIME_INTERVAL = 10, 60

P = 0.3
remote_addr=("10.206.0.88", 19909)
iplists = []
ipindex = 0
client2router = {}
ipidx_lock = threading.Lock()
sock_lock = threading.Lock()


if sys.platform == "win32":
    # On Windows, the best timer is time.clock()
    default_timer = time.clock
else:
    # On most other platforms the best timer is time.time()
    default_timer = time.time

# From /usr/include/linux/icmp.h; your milage may vary.
ICMP_ECHO_REQUEST = 8 # Seems to be the same on Solaris.

def msg( e ):
    today = time.strftime("%Y%m%d")
    error_log = file("/home/qspace/log/hx_ping_error_%s.log" % today, "a+")
    error_log.write( e + "\n" )
    error_log.flush()
    error_log.close()

def checksum(source_string):
    """
    I'm not too confident that this is right but testing seems
    to suggest that it gives the same answers as in_cksum in ping.c
    """
    sum = 0
    countTo = (len(source_string)/2)*2
    count = 0
    while count<countTo:
        thisVal = ord(source_string[count + 1])*256 + ord(source_string[count])
        sum = sum + thisVal
        sum = sum & 0xffffffff # Necessary
        count = count + 2

    if countTo<len(source_string):
        sum = sum + ord(source_string[len(source_string) - 1])
        sum = sum & 0xffffffff # Necessary?

    sum = (sum >> 16)  +  (sum & 0xffff)
    sum = sum + (sum >> 16)
    answer = ~sum
    answer = answer & 0xffff

    # Swap bytes. Bugger me if I know why.
    answer = answer >> 8 | (answer << 8 & 0xff00)

    return answer


def receive_one_ping(my_socket, ID, timeout, dest_addr):
    """
    receive the ping from the socket.
    """
    timeLeft = timeout
    while True:
        startedSelect = default_timer()
        whatReady = select.select([my_socket], [], [], timeLeft)
        
        howLongInSelect = (default_timer() - startedSelect)
        if whatReady[0] == []: # Timeout
            action_time = time.strftime("%Y-%m-%d %X")
            msg( "%s: %s timeout" % (action_time, dest_addr) )
            return

        timeReceived = default_timer()
        recPacket, addr = my_socket.recvfrom(1024)
        
        icmpHeader = recPacket[20:28]
        type, code, checksum, packetID, sequence = struct.unpack(
            "bbHHh", icmpHeader
        )
        
        if packetID == ID:
            bytesInDouble = struct.calcsize("d")
            timeSent = struct.unpack("d", recPacket[28:28 + bytesInDouble])[0]
            return  timeReceived

        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            action_time = time.strftime("%Y-%m-%d %X")
            msg( "%s: %s timeout" % (action_time, dest_addr) )
            return


def send_one_ping(my_socket, dest_addr, packet):
    """
    Send one ping to the given >dest_addr<.
    """
    dest_addr  =  socket.gethostbyname(dest_addr)
    t1 = default_timer()
    my_socket.sendto(packet, (dest_addr, 1)) # Don't know about the 1
    
    return t1
    
def do_one(packet, dest_addr, timeout, thread_id):
    """
    Returns either the delay (in seconds) or none on timeout.
    """
    try:
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, 1)
    except socket.error, (errno, e):
        if errno == 1:
            # Operation not permitted
            e = e + (
                " - Note that ICMP messages can only be sent from processes"
                " running as root."
            )
            raise socket.error(e)
        action_time = time.strftime("%Y-%m-%d %X")
        msg( "%s: %s %s" % (action_time, errno, e) )
        raise # raise the original error

    t1 = send_one_ping(my_socket, dest_addr, packet)
    t2 = receive_one_ping(my_socket, thread_id, timeout, dest_addr)

    my_socket.close()
    if t2 == None:
        return None

    return t2 - t1

def prechecksum(ID):
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    my_checksum = 0

    # Make a dummy heder with a 0 checksum.
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1)
    bytesInDouble = struct.calcsize("d")
    data = (192 - bytesInDouble) * "Q"
    data = struct.pack("d", 0) + data
    
    # Calculate the checksum on the data and the dummy header.
    my_checksum = checksum(header + data)

    # Now that we have the right checksum, we put that in. It's just easier
    # to make up a new header than to stuff it into the dummy.
    header = struct.pack(
        "bbHHh", ICMP_ECHO_REQUEST, 0, socket.htons(my_checksum), ID, 1
    )
    
    packet = header + data
    return packet

    

def verbose_ping(packet, dest_addr, timeout , count , thread_id):
    """
    Send >count< ping to >dest_addr< with the given >timeout< and display
    the result.
    """
    hit = 0.0
    ttl = 0.0

    for i in xrange(count):
        try:
            delay  =  do_one(packet, dest_addr,  timeout, thread_id)
        except socket.gaierror, e:
            break

        if delay  ==  None:
            hit+= 1
        else:
            ttl += delay
    if count - hit != 0:
        ttl = int( ttl * 1000000 / (count - hit) )
    hit = hit / count   
    return  hit, ttl


#################################################################################################

def load_sw_info(path):
    x = file(path)
    router2clients = {}
    for ln in x:
        client, nickname, router, area = ln.strip().split()

        client2router[client] = router
        router2clients.setdefault(router, []).append( client )
        
    return client2router, router2clients

def is_selected(n, p):
    import math, random
    np =  math.ceil(n * p)

    while True:
        r = random.randint(1, n)
        if r <= np:
            yield True
            continue
        
        yield False


def get_servers_iplist(router_from, router2clients):
    ips = []
    for key, value in router2clients.iteritems():
        if router_from != key:
            random.shuffle(value)
            ips.append( value[0] )
    return ips


def thread_ping(sock, thread_id):
    global iplists, ipindex, client2router, sock_lock, ipidx_lock
    iplen = len(iplists)
    ping_from = socket.gethostbyname( socket.gethostname() )

    packet = prechecksum(thread_id)
    
    while True:
        ipidx_lock.acquire()
        i = ipindex
        ipindex += 1
        ipidx_lock.release()
             
        
        ipidx_lock.acquire()
        if i >= iplen:
            ipidx_lock.release()
            break
        ipidx_lock.release()
      
        action_time = time.strftime("%Y-%m-%d %X")
        
        ping_to = iplists[i]

        loss, delay = verbose_ping(packet, ping_to, 0.3, PING_COUNT, thread_id)

        router_from = client2router[ping_from]
        router_to = client2router[ping_to]
        data = "wx:%s,%s,%s,%s,%s,%s,%s\n" % (action_time, ping_from, ping_to, router_from, router_to, loss, delay)
              
        try:
            sock_lock.acquire()
            sock.sendall( data )
        except socket.error:
            e = "%s:writing data to server case across error!" % action_time
            msg( e )
            
        
        sock_lock.release()

       
def main():
    #if exsited
    import os
    try:
        ps = file("/tmp/hx_ping").read()
        proc = "/proc/%s" % ps
        if os.path.exists(proc):
            #quit
            return
        
        pid = os.getpid()
        pid_file = file("tmp/hx_ping", "w")
        pid_file.write( str(pid) )
        pid_file.close()
        
        action_time = time.strftime("%Y-%m-%d %X")
        msg( "%s: ping process restarted again" % action_time )
    except IOError:
        file("/tmp/hx_ping", "w").write( str(os.getpid()) )

    #enter main loop
    global client2router, iplists, ipindex
    
    try:
        client2router, router2clients = load_sw_info("/home/qspace/upload/all_sw_info")
    except:
        os.system("rsync 172.27.19.230::upload/all_sw_info /home/qspace/upload/")
        client2router, router2clients = load_sw_info("/home/qspace/upload/all_sw_info")

    
    ping_from = socket.gethostbyname( socket.gethostname() )
    router_from = client2router[ping_from]

    n = len( router2clients[router_from] )
    xs = is_selected(n, P)

    sync_h, sync_m = random.randint(0, 23), random.randint(0, 59)
    while True:
        start_time = time.time()
        
        curr_time = time.localtime()
        h = curr_time.tm_hour
        m = curr_time.tm_min
        
        if  h == sync_h and m == sync_m:
            action_time = time.strftime("%Y-%m-%d %X")
            msg( "%s: update switch infomation" ) 
            os.system("rsync 172.27.19.230::upload/all_sw_info /home/qspace/upload/")
            client2router, router2clients = load_sw_info("/home/qspace/upload/all_sw_info")

        if not xs.next():
            end_time = time.time()
            interval = TIME_INTERVAL - (end_time - start_time)
            if interval > 0:
                time.sleep(TIME_INTERVAL - (end_time - start_time))
            continue

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect( remote_addr )

        iplists = get_servers_iplist(router_from, router2clients)
        ipindex = 0 # important
        
 
        t = []
        for i in xrange(1):
            t.append( threading.Thread( target = thread_ping, args = (sock,i) ) )

        
        for i in t:
            i.daemon = True
            i.start()

        for i in t:
            i.join()
        
        sock.close()

        end_time = time.time()
        interval = TIME_INTERVAL - (end_time - start_time)
        if interval < 0:
            action_time = time.strftime("%Y-%m-%d %X")
            e = "%s: processing ping wastes more than 1 min" % action_time
            msg( e )
        else:
            time.sleep( TIME_INTERVAL - (end_time - start_time) )


if __name__ == "__main__":
    main()
