#!/usr/bin/python
# coding=utf-8
import redis
import argparse
import os
import atexit
import signal
import sys
import json
import subprocess as sp

def daemonize(pidfile,    stdin='/dev/null',
                          stdout='/dev/null',
                          stderr='/dev/null'):
    if os.path.exists(pidfile):
        raise RuntimeError('Already running')

    # First fork (detaches from parent)
    try:
        if os.fork() > 0:
            raise SystemExit(0) # parent exit
    except OSError as e:
        raise RuntimeError('Fork #1 failed!')

    os.chdir('/')
    os.umask(0)
    os.setsid() # child process become session and group leader process

    # Second fork (relinquish session leadership)
    try:
        if os.fork() > 0:
            raise SystemExit(0)
    except OSError as e:
        raise RuntimeError('Fork #2 failed!')

    # Flush I/O buffers
    #sys.stdout.flush()
    #sys.stderr.flush()

    # Replace file description for stdin, stdout, stderr
    with open(stdin, 'rb', 0) as f:
        os.dup2(f.fileno(), sys.stdin.fileno())
    with open(stdout, 'ab+', 0) as f:
        os.dup2(f.fileno(), sys.stdout.fileno())
    with open(stderr, 'ab+', 0) as f:
        os.dup2(f.fileno(), sys.stderr.fileno())

    # write the PID file
    with open(pidfile, 'w') as f:
        print >> f, os.getpid()

    # Arrange to have the PID file removed on exit/signal
    atexit.register(lambda: os.remove(pidfile))

    # Signal handler for termination (required)
    def sigterm_handler(signo, frame):
        raise SystemExit(1)

    signal.signal(signal.SIGTERM, sigterm_handler)

def cpu_test(time, connection, IP):
    logname = "/var/log/mario/"+"cpu-"+time+".log"
    errorinfo=''
    # exec cpu test
    proc = sp.Popen('sysbench --threads=`cat /proc/cpuinfo | grep processor | wc -l`  --events=20000 cpu --cpu-max-prime=50000 run', shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    out = proc.communicate()
    with open(logname, 'w') as logfile:
        # stdout
        if out[0]:
            logfile.write(out[0])
        # stderr, both write to logfile
        if out[1]:
            logfile.write(out[1])
            errorinfo+=out[1]
        if errorinfo:
            # send error info to server
            print errorinfo
            result_json = {
                'type': 'cpu',
                'IP': IP,
                'success': False,
                'deployTime': time,
                'pmerrorInfo': errorInfo
            }
            result_str = json.dumps(result_json)
            recv_num = connection.publish("%s:RESULT" % IP, result_str)
            if recv_num < 1:
                print "Test Server may not recive cpu test error info at %s\n" % time
            return False
    # get result from log file
    readproc = sp.Popen("cat %s | grep 'total time' | awk '{print $3}'" % logname, shell=True, stderr=sp.PIPE, stdout=sp.PIPE)
    out1 = readproc.communicate()
    result=''
    result+=out1[0]
    print "result: ", result
    if result:
        re= float(result.strip('s\n'))
        # send result to server
        result_json = {
                'type': 'cpu',
                'IP': IP,
                'success': True,
                'deployTime': time,
                'pmresult': re
        }
        result_str = json.dumps(result_json)
        recv_num = connection.publish("%s:RESULT" % IP, result_str)
        if recv_num < 1:
            print "Test Server may not recive cpu test result at %s\n" % time
        else:
            print "Send %s cpu test result to test server.\n" % time
        return True
    else:
        print "Extract result from %s cpu test log file encounters error!\n" % time
        return False


def mem_test(time, connection, IP):
    logname = "/var/log/mario/"+"mem-"+time+".log"
    errorinfo=''
    # exec mem test
    proc = sp.Popen('./stream-allcores', shell=True, stdout=sp.PIPE, stderr=sp.PIPE, cwd='/usr/local/src/stream/')
    out = proc.communicate()
    with open(logname, 'w') as logfile:
        # stdout
        if out[0]:
            logfile.write(out[0])
        # stderr, both write to logfile
        if out[1]:
            logfile.write(out[1])
            errorinfo+=out[1]
        if errorinfo:
            # send error info to server
            print errorinfo
            result_json = {
                'type': 'mem',
                'IP': IP,
                'success': False,
                'deployTime': time,
                'pmerrorInfo': errorInfo
            }
            result_str = json.dumps(result_json)
            recv_num = connection.publish("%s:RESULT" % IP, result_str)
            if recv_num < 1:
                print "Test Server may not recive mem test error info at %s\n" % time
            return False
    # get result from log file
    readproc = sp.Popen("cat /root/mem.log | grep 'Triad' | awk '{print $2}'", shell=True, stderr=sp.PIPE, stdout=sp.PIPE)
    out1 = readproc.communicate()
    result=''
    result+=out1[0]
    # print "result: ", result
    if result:
        result_num = [ float(num.strip()) for num in result.split() ]
        average = reduce(lambda x,y: x+y, result_num) / 10
        # send result to server
        result_json = {
                'type': 'mem',
                'IP': IP,
                'success': True,
                'deployTime': time,
                'pmresult': average 
        }
        result_str = json.dumps(result_json)
        recv_num = connection.publish("%s:RESULT" % IP, result_str)
        if recv_num < 1:
            print "Test Server may not recive mem test result at %s\n" % time
        else:
            print "Send %s mem test result to test server.\n" % time
        return True
    else:
        print "Extract result from %s mem test log file encounters error!\n" % time
        return False

def io_test(time, connection, IP):
    logname = "/var/log/mario/"+"io-"+time+".log"
    errorinfo=''
    # exec mem test
    proc = sp.Popen('/usr/local/src/iozone3_465/src/current/iozone \
                    -l `cat /proc/cpuinfo | grep processor | wc -l` \
                    -u `cat /proc/cpuinfo | grep processor | wc -l` \
                    -i 0 -i 1 -b %s' % logname, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    out = proc.communicate()
    with open(logname, 'w') as logfile:
        # stdout
        if out[0]:
            logfile.write(out[0])
        # stderr, both write to logfile
        if out[1]:
            logfile.write(out[1])
            errorinfo+=out[1]
        if errorinfo:
            # send error info to server
            print errorinfo
            result_json = {
                'type': 'io',
                'IP': IP,
                'success': False,
                'deployTime': time,
                'pmerrorInfo': errorInfo
            }
            result_str = json.dumps(result_json)
            recv_num = connection.publish("%s:RESULT" % IP, result_str)
            if recv_num < 1:
                print "Test Server may not recive io test error info at %s\n" % time
            return False
    # get result from log file
    readproc = sp.Popen("cat %(logname)s | grep 'Initial write' | awk '{print $5}' && \
                        cat %(logname)s | grep -e 'Rewrite'  -e 'Read' -e 'Re-read' | awk {'print $4}'" % {'logname': logname},
                        shell=True, stderr=sp.PIPE, stdout=sp.PIPE)
    out1 = readproc.communicate()
    result=''
    result+=out1[0]
    # print "result: ", result
    if result:
        result_num = [ float(num.strip()) for num in result.split() ]
        # send result to server
        result_json = {
                'type': 'io',
                'IP': IP,
                'success': True,
                'deployTime': time,
                'pmInitialWrite': result_num[0],
                'pmRewrite': result_num[1],
                'pmRead': result_num[2],
                'pmReRead': result_num[3]
        }
        result_str = json.dumps(result_json)
        recv_num = connection.publish("%s:RESULT" % IP, result_str)
        if recv_num < 1:
            print "Test Server may not recive io test result at %s\n" % time
        else:
            print "Send %s io test result to test server.\n" % time
        return True
    else:
        print "Extract result from %s io test log file encounters error!\n" % time
        return False


# code executed in daemon process
def main():
    # test if the daemon work properly
    import time
    sys.stdout.write('{0} Daemon started with pid {1}\n'.format(time.ctime(), os.getpid()))
    """
    while True:
        sys.stdout.write('Daemon alive! {}\n'.format(time.ctime()))
        time.sleep(10)
    """
    conn = redis.StrictRedis(host=args.marioip, port=6379, db=5)
    # ignore subscribe/unsubscribe confirmation messages
    p = conn.pubsub(ignore_subscribe_messages=True)
    p.subscribe(args.ip)
    while True:
        message = p.get_message()
        if message:
            print message
            message_json = json.loads(message['data'])
            # print message_json
            #print 'type of message[data]: ', type(message['data']), message['data']
            if message_json['type'] == 'cpu':
                if cpu_test(message_json['time'], conn, args.ip) == False:
                    print 'sysbench benchmark test or extract result from log file failed!\n'
            elif message_json['type'] == 'mem':
                if mem_test(message_json['time'], conn, args.ip) == False:
                    print 'stream benchmark test or extract result from log file failed!\n'
            elif message_json['type'] == 'io':
                if io_test(message_json['time'], conn, args.ip) == False:
                    print 'iozone benchmark test or extract result from log file failed!\n'
        #time.sleep(0.001)

if __name__ == '__main__':
    PIDFILE = '/tmp/mariodaemon.pid'

    parser = argparse.ArgumentParser(usage='./%(prog)s(python %(prog)s) [start|stop] [options]',
                                description="""
                                This daemon is used to listen test events from Mario app, at the very begining,
                                you start daemon with the IP address which is the server exposed to the Mario app.
                                Also you should specify Mario app server IP address.
                                """)

    parser.add_argument("operation", help="[start|stop|status] the daemon")
    parser.add_argument("--ip", help="the IP addr server exposed to Mario app")
    parser.add_argument("-mip","--marioip", help="the IP addr of Mario app", default="10.214.16.200")
    args = parser.parse_args()

    if args.operation == 'start':
        sys.stdout.write('daemon start!\n')
        try:
            daemonize(PIDFILE,
                    stdout='/var/log/mario/mariodaemon.log',
                    stderr='/var/log/mario/mariodaemon.log')
        except RuntimeError as e:
            print >> sys.stderr, e
            raise SystemExit(1)
        main()
    elif args.operation == 'stop':
        if os.path.exists(PIDFILE):
            with open(PIDFILE) as f:
                os.kill(int(f.read()), signal.SIGTERM) # The PIDFILE stores the daemon pid
        else:
            print >> sys.stderr, "Not Running"
            raise SystemExit(1)
    elif args.operation == 'status':
        if os.path.exists(PIDFILE):
            print "running"
            raise SystemExit(0)
        else:
            print "stop"
            raise SystemExit(1)
    else:
        print >> sys.stderr, 'Unknown command {!r}'.format(args.operation)


