#!/usr/bin/python 
#author valleyhe
#last update 2013/3/20

import time, MySQLdb, os, struct, socket


def write_log(msg):
    today = time.strftime("%Y%m%d")
    log = file("/home/qspace/log/update_sql_error_%s.log" % today, "a+")
    log.write(msg + "\n")
    #write stream into file now
    log.flush()
    log.close()
    

def ip2int(ip):
    return struct.unpack("!I",socket.inet_aton(str(ip)))[0]


def update_sw():
    last_load_time = None
    sw_path = "/home/qspace/upload/all_sw_info"
    if os.path.exists("/tmp/hx_sw_mmtime"):
        last_load_time = int( file("/tmp/hx_sw_mmtime").read() )

    action_time = time.strftime("%Y%m%d %X")
    
    if os.path.exists(sw_path):
        mtime = os.path.getmtime(sw_path)
    else:
        
        write_log( "%s: %s don't exist." % (action_time, sw_path) )
        return

    if mtime > last_load_time or last_load_time == None:
        file("/tmp/hx_sw_mmtime", "w").write( str(mtime) )

        db = MySQLdb.connect(host="10.151.18.233", user="qspace", passwd="forconnect", db="delayinfo")
        c = db.cursor()

        #delete original data
        cmd = "truncate table ip2sw"
        c.execute(cmd)
        db.commit()

        cmd = "INSERT INTO ip2sw(ip, location, sw_ip) VALUES"
        for ln in file(sw_path):
            ip, location, location_ip = ln.strip().split()[0:-1]
            cmd += "('%s', '%s', '%s')," % (ip, location, location_ip)
        cmd = cmd[0:-1]
        c.execute( cmd )
        db.commit()

        c.close()
        db.close()

        write_log( "%s: update all_sw_info successfully." % action_time )
    else:
        write_log( "%s: don't need to update all_sw_info successfully." % action_time )
    

def main():
    
    update_sw()
    
    try:
        ps = file("/tmp/hx_update_sql").read()
        proc = "/proc/%s" % ps
        if os.path.exists(proc):
            #quit
            return    
        file("/tmp/hx_update_sql", "w").write( str( os.getpid() ) )
    except IOError:
        file("/tmp/hx_update_sql", "w").write( str(os.getpid()) )
    
    action = time.strftime("%Y-%m-%d %X")
    
    today = time.strftime("%Y%m%d%H")
    curr_log_file = "/home/qspace/log/wxdelayinfo_%s.log" % today
    
    try:
        last_file, last_tell = file("/tmp/hx_last_locate_ip", "r").read().split()
    except IOError:
        last_file, last_tell = curr_log_file, 0

    last_tell = int(last_tell)
    
    if os.path.exists( last_file ):
        log = file(last_file, "r")
    else:
        last_file, last_tell = curr_log_file, 0
        if os.path.exists( last_file ):
            log = file( last_file, "r" )
        else:
            return 
        
    log.seek( last_tell )

    data = log.readlines()
    
    if len(data) == 0:
        #if robert will read next file.
        last_file_name = os.path.basename( last_file )
        last_time = last_file_name.split(".")[0].split("_")[1]
        if today <= last_time:
            return 
        
        last_file = curr_log_file
        last_tell = 0
        try:
            log = file( last_file )
        except IOError:
            write_log( "%s: open %s error, don't exist." % (action, last_file ) )
            return 
        data = log.readlines()
    
    if not data:
        return     

    try:
        db = MySQLdb.connect(host="10.151.18.233", user="qspace", passwd="forconnect", db="delayinfo")
        c = db.cursor()
    except MySQLdb.MySQLError, e:
        e = "%s %s" % (action, e)
        write_log( e )
        return 
    
    hash_tables = {}
    for i in xrange(1000):
        hash_tables[i] = []
    
    cur_sum = 0
    for ln in data:
        cur_sum += len( ln )
        ln = ln.strip().split(",")
        ip_from = ip2int( ln[1] )
        ip_to = ip2int( ln[2] )
        table_nr = ip_from % 1000
        
        ln[1] = ip_from
        ln[2] = ip_to
        hash_tables[table_nr].append( tuple(ln) )
    
    for key, values in hash_tables.iteritems():
        if not values:
            continue
        cmd = "INSERT INTO ip2ip_%s (action_time, ip_from, ip_to, delay, loss) VALUES" % key
        cmd += ",".join("('%s', %s, %s, %s, %s)" % ln for ln in values)
        c.execute( cmd )
        db.commit()
            
    last_tell += cur_sum
    c.close()
    db.close()
    
    file("/tmp/hx_last_locate_ip", "w").write( "%s %s" % (last_file, last_tell) )    

if __name__ == "__main__":
    main()
