#!/usr/bin/python
import redis
import argparse
import os
import atexit
import signal
import sys

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
    sys.stdout.flush()
    sys.stderr.flush()

    # Replace file description for stdin, stdout, stderr
    with open(stdin, 'rb', 0) as f:
        os.dup2(f.fileno(), sys.stdin.fileno())
    with open(stdout, 'ab', 0) as f:
        os.dup2(f.fileno(), sys.stdout.fileno())
    with open(stderr, 'ab', 0) as f:
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

# code executed in daemon process
def main():
    # test if the daemon work properly
    import time
    sys.stdout.write('Daemon started with pid {}\n'.format(os.getpid()))
    while True:
        sys.stdout.write('Daemon alive! {}\n'.format(time.ctime()))
        time.sleep(10)
   
"""
    conn = redis.StrictRedis(host=args.marioip, port=6379, db=5)
    p = conn.pubsub()
    p.subscribe(args.ip)
    while True:
        message = p.get_message()
        if message:
            print message
        time.sleep(0.001)    
"""


if __name__ == '__main__':
    PIDFILE = '/tmp/mariodaemon.pid'

    parser = argparse.ArgumentParser(usage='./%(prog)s(python %(prog)s) [start|stop] [options]',
                                description="""
                                This daemon is used to listen test events from Mario app, at the very begining,
                                you start daemon with the IP address which is the server exposed to the Mario app.
                                Also you should specify Mario app server IP address.
                                """)

    parser.add_argument("operation", help="[start|stop] the daemon")
    parser.add_argument("--ip", help="the IP addr server exposed to Mario app")
    parser.add_argument("-mip","--marioip", help="the IP addr of Mario app", default="10.214.16.200")
    args = parser.parse_args()

    if args.operation == 'start':
        try:
            daemonize(PIDFILE,
                    stdout='/tmp/mariodaemon.log',
                    stderr='/tmp/mariodaemon.log')
        except RuntimeError as e:
            print >> sys.stderr, e
            raise SystemExit(1)

        main()

    elif args.operation == 'stop':
        if os.path.exists(PIDFILE):
            with open(PIDFILE) as f:
                os.kill(int(f.read()), signal.SIGTERM) # The PIDFILE stores the daemon pid
        else:
            print >> sys.stderr, e
            raise SystemExit(1)

    else:
        print >> sys.stderr, 'Unknown command {!r}'.format(args.operation)
                
        
