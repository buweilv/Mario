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
from subprocess import CalledProcessError
import xml.etree.ElementTree as ET
import random
import time
import paramiko

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

def get_ip_from_mac(mac):
	return sp.check_output("virsh net-dhcp-leases default %(mac)s | grep %(mac)s | awk '{print $5}'" % {'mac': mac}, shell=True).strip()[:-3]

def connect_vm(vm_ip):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=vm_ip, port=22,username= "root", password="vm123456") # all vm default user/password
    return ssh

def generate_config(type, mem, cpu_cores):
    """
    * create vm config file: VM CPU cores same as the pm, VM mem half of the pm and vm incremental qcow2 format image
    """
    mac = [ 0x52, 0x54, 0x00,
           random.randint(0x00, 0x7f),
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff) ]
    mac_addr = ':'.join(map(lambda x: "%02x" % x, mac))
    sp.call("qemu-img create -f qcow2 -b /mnt/mfs/sl6-bk.img /var/lib/libvirt/images/vm-%(type)s.qcow2" % {'type': type}, shell=True)
    if not sp.call("grep -q -i 'release 7' /etc/redhat-release", shell=True):
        tree = ET.ElementTree(file="/mnt/mfs/base_rhel7.xml")
    if not sp.call("grep -q -i 'release 6' /etc/redhat-release", shell=True):
        tree = ET.ElementTree(file="/mnt/mfs/base_rhel6.xml")
    tree.find('name').text = "%(type)s-vm" % {'type': type}
    tree.find('memory').text = str(mem / 2)
    tree.find('currentMemory').text = str(mem / 2)
    tree.find('vcpu').text = str(cpu_cores)
    tree.find('devices/interface[@type="network"]/mac').attrib['address'] = mac_addr
    tree.find('devices/disk[@device="disk"]/source').attrib['file'] = "/var/lib/libvirt/images/vm-%(type)s.qcow2" % {'type': type}
    tree.write('/var/log/mario/%(type)s-vm.xml' % {'type': type})
    return mac_addr

def pm_test(type, pm_ip, deploy_time, pm_logname, connection):
    """
    execute specified type test
    """
    if type == "cpu":
        proc = sp.Popen('sysbench --threads=`cat /proc/cpuinfo | grep processor | wc -l`  --events=20000 cpu --cpu-max-prime=50000 run', shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    elif type == "mem":
        proc = sp.Popen('./stream-allcores', shell=True, stdout=sp.PIPE, stderr=sp.PIPE, cwd='/usr/local/src/stream/')
    elif type == "io":
        proc = sp.Popen('/usr/local/src/iozone3_465/src/current/iozone \
                        -l `cat /proc/cpuinfo | grep processor | wc -l` \
                        -u `cat /proc/cpuinfo | grep processor | wc -l` \
                        -i 0 -i 1 -b %s' % pm_logname, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    else:
        print "No specified type, when execute function pm_test"
        return False
    out = proc.communicate()
    errorinfo = ''
    with open(pm_logname, 'w') as logfile:
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
                'type': type,
                'IP': pm_ip,
                'success': False,
                'deployTime': deploy_time,
                'pmerrorInfo': errorinfo
            }
            result_str = json.dumps(result_json)
            recv_num = connection.publish("%s:RESULT" % pm_ip, result_str)
            if recv_num < 1:
                print "Test Server may not recive %(type)s test error info at %(time)s\n" % {'type': type, 'time': deploy_time}
            return False
        else:
            return True

def get_vm_ip(type, pm_ip, mac_addr, deploy_time, connection):
    """
    start vm and get ip from mac
    """
    try:
        sp.check_call("virsh create /var/log/mario/%s-vm.xml" % type, shell=True)
        #print "vm mac: ", mac_addr
        time.sleep(30)
        wait_num = 10
        vm_ip = get_ip_from_mac(mac_addr)
        while not vm_ip:
            if wait_num > 0:
                print "trying to get vm ip from mac"
                wait_num -= 1
                time.sleep(5)
                vm_ip = get_ip_from_mac(mac_addr)
            else:
                break
        return vm_ip
    except CalledProcessError as cpe:
        print cpe
        result_json = {
            'type': 'cpu',
            'IP': pm_ip,
            'success': False,
            'deployTime': deploy_time,
            'pmerrorInfo': "vm failed to start"
        }
        result_str = json.dumps(result_json)
        recv_num = connection.publish("%s:RESULT" % pm_ip, result_str)
        if recv_num < 1:
            print "Test Server may not recive cpu test error info at %s\n" % deploy_time
        return None

def vm_test(type, vm_ip, pm_ip, deploy_time, vm_logname, connection):
    """
    * ssh connect to vm
    * ssh exec benchmark
    """
    wait_num = 10
    time.sleep(30) # wait for sshd starts in vm
    while True:
        try:
            ssh = connect_vm(vm_ip)
            break
        except paramiko.ssh_exception.NoValidConnectionsError as e:
            if wait_num > 0:
                print "trying to connect to vm..."
                time.sleep(5)
                wait_num-=1
                continue
            else:
                print "SSH Connection Failed: ", e.errors[(vm_ip, 22)]
                result_json = {
                    'type': type,
                    'IP': pm_ip,
                    'success': False,
                    'deployTime': deploy_time,
                    'pmerrorInfo': "Failed to connect vm from host."
                }
                result_str = json.dumps(result_json)
                recv_num = connection.publish("%s:RESULT" % pm_ip, result_str)
                if recv_num < 1:
                    print "Test Server may not recive cpu test error info at %s\n" % deploy_time
                if ssh:
                    ssh.close()
                return False
    print "connect to vm ip: ", vm_ip
    if type == "cpu":
        stdin,stdout,stderr = ssh.exec_command('sysbench --threads=`cat /proc/cpuinfo | grep processor | wc -l`  --events=20000 cpu --cpu-max-prime=50000 run')
    elif type == "mem":
        print "begin exec stream"
        stdin,stdout,stderr = ssh.exec_command('cd /usr/local/src/stream/; ./stream-allcores')
        print "finish exec stream"
    elif type == "io":
        # if there is no -b, no summary will be printed...
        stdin,stdout,stderr = ssh.exec_command('/usr/local/src/iozone3_465/src/current/iozone \
                    -l `cat /proc/cpuinfo | grep processor | wc -l` \
                    -u `cat /proc/cpuinfo | grep processor | wc -l`  -i 0 -i 1 -b iozone.log')
    else:
        print "No specified type when call function vm_test"
        return False
    with open(vm_logname, "w") as vm_logfile:
        vm_logfile.write(stdout.read())
        vm_errorinfo = stderr.read()
        if vm_errorinfo:
            vm_logfile.write(vm_errorinfo)
            print "vm run %(type)s benchmark encounters error:\n" % {'type': type}, vm_errorinfo
            result_json = {
                'type': type,
                'IP': pm_ip,
                'success': False,
                'deployTime': deploy_time,
                'vmerrorInfo': vm_errorinfo
            }
            result_str = json.dumps(result_json)
            recv_num = connection.publish("%s:RESULT" % pm_ip, result_str)
            if recv_num < 1:
                print "Test Server may not recive vm  cpu test error info at %s\n" % deploy_time
            if ssh:
                ssh.close()
            return False
        else:
            return True

def get_result(type,  pm_ip, deploy_time, pm_logname, vm_logname, connection):
    if type == "cpu":
        readproc = sp.Popen("cat %s | grep 'total time' | awk '{print $3}'" % pm_logname, shell=True, stderr=sp.PIPE, stdout=sp.PIPE)
        vm_readproc = sp.Popen("cat %s | grep 'total time' | awk '{print $3}'" % vm_logname, shell=True, stderr=sp.PIPE, stdout=sp.PIPE)
    elif type == "mem":
        readproc = sp.Popen("cat %s | grep 'Triad' | awk '{print $2}'" % pm_logname, shell=True, stderr=sp.PIPE, stdout=sp.PIPE)
        vm_readproc = sp.Popen("cat %s | grep 'Triad' | awk '{print $2}'" % pm_logname, shell=True, stderr=sp.PIPE, stdout=sp.PIPE)
    elif type == "io":
        readproc = sp.Popen("cat %(logname)s | grep 'Initial write' | awk '{print $5}' && \
                            cat %(logname)s | grep -e 'Rewrite'  -e 'Read' -e 'Re-read' | awk {'print $4}'" % {'logname': pm_logname},
                            shell=True, stderr=sp.PIPE, stdout=sp.PIPE)
        vm_readproc = sp.Popen("cat %(logname)s | grep 'Initial write' | awk '{print $5}' && \
                            cat %(logname)s | grep -e 'Rewrite'  -e 'Read' -e 'Re-read' | awk {'print $4}'" % {'logname': vm_logname},
                            shell=True, stderr=sp.PIPE, stdout=sp.PIPE)
    else:
        print "No specified type when call function get_result"
        return False
    pm_out = readproc.communicate()
    vm_out = vm_readproc.communicate()
    pm_result = pm_out[0]
    vm_result = vm_out[0]
    print "pm result: ", pm_result, "vm_result: ", vm_result
    if pm_result and vm_result:
        if type == "cpu":
            pm_re= float(pm_result.strip('s\n'))
            vm_re= float(vm_result.strip('s\n'))
            # send result to server
            result_json = {
                    'type': 'cpu',
                    'IP': pm_ip,
                    'success': True,
                    'deployTime': deploy_time,
                    'pmresult': pm_re,
                    'vmresult': vm_re
            }
        elif type == "mem":
            pm_result_num = [ float(num.strip()) for num in pm_result.split() ]
            pm_average = reduce(lambda x,y: x+y, pm_result_num) / 10
            vm_result_num = [ float(num.strip()) for num in vm_result.split() ]
            vm_average = reduce(lambda x,y: x+y, vm_result_num) / 10
            result_json = {
                    'type': 'mem',
                    'IP': pm_ip,
                    'success': True,
                    'deployTime': deploy_time,
                    'pmresult': pm_average,
                    'vmresult': vm_average
            }
        elif type == "io":
            pm_result_num = [ float(num.strip()) for num in pm_result.split() ]
            vm_result_num = [ float(num.strip()) for num in vm_result.split() ]
            result_json = {
                    'type': 'io',
                    'IP': pm_ip,
                    'success': True,
                    'deployTime': deploy_time,
                    'pmInitialWrite': pm_result_num[0],
                    'pmRewrite': pm_result_num[1],
                    'pmRead': pm_result_num[2],
                    'pmReRead': pm_result_num[3],
                    'vmInitialWrite': vm_result_num[0],
                    'vmRewrite': vm_result_num[1],
                    'vmRead': vm_result_num[2],
                    'vmReRead': vm_result_num[3]
            }
        result_str = json.dumps(result_json)
        recv_num = connection.publish("%s:RESULT" % pm_ip, result_str)
        if recv_num < 1:
            print "Test Server may not recive %(type)s test result at %(time)s\n" % {'type': type, 'time': deploy_time}
        else:
            print "Send %(time)s %(type)s test result to test server.\n" % {'type': type, 'time': deploy_time}
        return True
    else:
        print "Extract result from %(time)s %(type)s test log file encounters error!\n" % {'type': type, 'time': deploy_time}
        return False

def virtualization_test(type, deploy_time, connection, IP, cpu_cores, mem):
    """
    virtualization_test function integrated all types of virtualization test, the type paramater is necessary to distinguish which
    type of virtualization test should be executed. Otherwise, we will write each kind of virtualization test, such as, cpu_test, mem_test,
    io_test etc, this is stupid.
    """
    pm_logname = "/var/log/mario/"+"%s-" % type + deploy_time + ".log"
    vm_logname = "/var/log/mario/"+"vm-%s-" % type + deploy_time + ".log"
    # exec pm test first
    if pm_test(type, IP, deploy_time, pm_logname, connection):
        mac_addr = generate_config(type, mem, cpu_cores)
        vm_ip = get_vm_ip(type, IP, mac_addr, deploy_time, connection)
        if vm_ip:
            return vm_test(type, vm_ip, IP, deploy_time, vm_logname, connection) and get_result(type, IP, deploy_time, pm_logname, vm_logname, connection)
        else:
            print "get vm ip failed!"
            return False
    else:
        print "pm %s test failed" % type
        return False


def terminateVM(type):
    """
    destroy vm and remove vm config file and qcow2 image
    """
    try:
        sp.check_call("virsh destroy %(type)s-vm && rm -f /var/lib/libvirt/images/vm-%(type)s.qcow2 && rm -f /var/log/mario/%(type)s-vm.xml" % {'type': type}, shell=True)
    except CalledProcessError as cpe:
        print "failed to delete vm-%(type)s.xml and vm-%(type)s.qcow2\n" % {'type': type}, cpe


# code executed in daemon process
def main():
    # test if the daemon work properly
    sys.stdout.write('{0} Daemon started with pid {1}\n'.format(time.ctime(), os.getpid()))
    """
    while True:
        sys.stdout.write('Daemon alive! {}\n'.format(time.ctime()))
        time.sleep(10)
    """
    # all paramiko connection will be logged here
    paramiko.util.log_to_file("/var/log/mario/paramiko.log")
    # Get CPU and memory info
    cpu_cores = int(sp.check_output("cat /proc/cpuinfo | grep 'processor' | wc -l ", shell=True))
    #mem =  int(float(sp.check_output("free -mh | grep Mem | awk '{print $2}'", shell=True).strip('G\n')))
    mem =  int(float(sp.check_output("free -mg | grep Mem | awk '{print $2}'", shell=True)))
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
            if not virtualization_test(message_json['type'], message_json['time'], conn, args.ip, cpu_cores, mem):
                print '%s type virtualization test failed!' % message_json['type']
            terminateVM(message_json['type'])
            """
            if message_json['type'] == 'cpu':
                if cpu_test(message_json['time'], conn, args.ip, cpu_cores, mem) == False:
                    print 'sysbench benchmark test or extract result from log file failed!\n'
                terminateVM('cpu')
            elif message_json['type'] == 'mem':
                if mem_test(message_json['time'], conn, args.ip, cpu_cores, mem) == False:
                    print 'stream benchmark test or extract result from log file failed!\n'
                terminateVM('mem')
            elif message_json['type'] == 'io':
                if io_test(message_json['time'], conn, args.ip) == False:
                    print 'iozone benchmark test or extract result from log file failed!\n'
                terminateVM('io')
            """
        #time.sleep(0.001)

if __name__ == '__main__':
    PIDFILE = '/tmp/mariodaemon.pid'

    parser = argparse.ArgumentParser(usage='./%(prog)s(python2.7 %(prog)s) [start|stop] [options]',
                                description="""
                                This daemon is used to listen test events from Mario app, at the very begining,
                                you start daemon with the IP address which is the server exposed to the Mario app.
                                Also you should specify Mario app server IP address.
                                """)

    parser.add_argument("operation", help="[start|stop|status] the daemon")
    parser.add_argument("--ip", help="the IP addr server exposed to Mario app")
    # read mario ip from appconfig
    with open("appconfig", 'r') as f:
        mario_ip = f.read()
    print "App server is: ", mario_ip
    parser.add_argument("-mip","--marioip", help="the IP addr of Mario app", default=mario_ip)
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


