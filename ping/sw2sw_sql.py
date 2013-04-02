#!/usr/bin/python 
#author valleyhe
#last update 2013/03/26

import time, MySQLdb, os

def load_sw_info(path):
    x = file(path)
    router2clients = {}
    client2router = {}
    for ln in x:
        client, nickname, router, area = ln.strip().split()

        client2router[client] = router
        router2clients.setdefault(router, []).append( client )
    
    return client2router, router2clients
    
def write_log(msg):
    today = time.strftime("%Y%m%d")
    log = file("/home/qspace/log/update_sql_sw_error_%s.log" % today, "a+")
    log.write(msg + "\n")
    #write stream into file now
    log.flush()
    log.close()    


def main():
    
    try:
        ps = file("/tmp/hx_update_sql_sw").read()
        proc = "/proc/%s" % ps
        if os.path.exists(proc):
            return         
    except IOError:
        pass
    
    file("/tmp/hx_update_sql_sw", "w").write( str( os.getpid() ) )     
    
    c2r, r2c = load_sw_info( "/home/qspace/upload/all_sw_info" )    
    
    today = time.strftime("%Y%m%d%H")
    curr_log_file = "/home/qspace/log/wxdelayinfo_%s.log" % today
    
    try:
        last_file, last_tell = file("/tmp/hx_last_locate_sw", "r").read().split()
    except IOError:
        last_file, last_tell = curr_log_file, 0

    last_tell = int(last_tell)
    
    action = time.strftime("%Y-%m-%d %X")        
    if os.path.exists( last_file ):
        log = file(last_file, "r")
    else:
        last_file, last_tell = curr_log_file, 0
        if os.path.exists( last_file ):
            log = file(last_file)
        else:
            write_log("%s %s not exsits!" % (action, last_file))
            return 
        
    log.seek( last_tell )

    data = log.readlines()
   
    try:
        db = MySQLdb.connect(host="10.151.18.233", user="qspace", passwd="forconnect", db="delayinfo")
        c = db.cursor()
    except MySQLdb.MySQLError, e:
        e = "%s %s" % (action, e)
        write_log( e )
        return 
    
    last_time = None  
    same_time_lns = []
    
    cur_sum = 0    
    for idx, ln in enumerate( data ):
        cur_sum += len( ln )
        
        this_ln_time = ln.split(",")[0].strip()
        this_ln_time = this_ln_time[:-2] + "00"
        
        if last_time !=  this_ln_time or idx == len(data) - 1:
            sw2sw = {}
            sw2sw_loss = {}
            sw2sw_count = {}
            
            for s_ln in same_time_lns:
                t, from_ip, to, delay, loss = s_ln.strip().split(",")
                
                delay = float(delay)
                loss = float(loss)
                try:
                    sw_from, sw_to = c2r[from_ip], c2r[to]
                    sw2sw[sw_from][sw_to] = sw2sw.setdefault( sw_from, {} ).setdefault( sw_to, 0) + delay
                    sw2sw_loss[sw_from][ sw_to ] =  sw2sw_loss.setdefault( sw_from , {}).setdefault( sw_to, 0) + loss
                    sw2sw_count[sw_from][sw_to]  = sw2sw_count.setdefault( sw_from, {}).setdefault( sw_to, 0) + 1
                except:
                    pass
            
            for sw_from, value in sw2sw.iteritems():
                sql_cmd = "INSERT INTO sw2sw(action_time, sw_from, sw_to, delay, loss) VALUES"
                for sw_to, delay in value.iteritems():
                    d = int(delay / sw2sw_count[sw_from][sw_to])
                    l = int( sw2sw_loss[sw_from][sw_to] / sw2sw_count[sw_from][sw_to] )
                    sql_cmd += "('%s','%s','%s',%s,%s)," % (last_time, sw_from, sw_to, d, l)
                c.execute( sql_cmd[:-1] )
                db.commit()
            
            del same_time_lns[:]
            last_time = this_ln_time
        
        same_time_lns.append( ln )
    last_tell += cur_sum
    
    file("/tmp/hx_last_locate_sw", "w").write( "%s %s" % (last_file, last_tell) )    

    c.close()
    db.close()

if __name__ == "__main__":
    main()
