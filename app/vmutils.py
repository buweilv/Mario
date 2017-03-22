# coding=utf-8
import fabric
import os
from fabric.api import execute, settings, run, abort, put, cd, env
from fabric.network import disconnect_all
from config import Config
from threading import Thread
from flask import g
from . import db, conn
from .models import Host, CPUResult, MemResult, IOResult
import redis
from sqlalchemy.exc import IntegrityError
import json

workdir = Config.WORK_DIR
mountdir = Config.MFS_MOUNT_POINT
mfsmaster = Config.MFS_MASTER
mario_ip = Config.MARIO_IP
# host = "10.214.144.181"
env.user = "root"
#env.password = "root"
baseimg = mountdir + "centos7-bk.img"
basexml = mountdir + "host-base.xml"
redistar = mountdir + "redis-2.10.5.tar.gz"
sysbenchtar = mountdir + "sysbench-1.0.1.tar.gz"
iozonetar = mountdir + "iozone3_465.tar"
streamtar = mountdir + "stream.tar"
daemonpy = mountdir + "daemon.py"
destroyvmpy = mountdir + "destroy_all_vms.py"
client6_rpm = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir,
                          'tools/moosefs-client-3.0.88-1.rhsysv.x86_64.rpm'))
client7_rpm = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir,
                          'tools/moosefs-client-3.0.86-1.rhsystemd.x86_64.rpm'))

def prepareVM(host):
    """
    prepare for the VM creation:
        * create work dir
        * install mfs client
        * disable iptable
        * create mfsmount dir
        * mount mfs
        * install redis-py  maybe even pip not installed, basically network connect to the Internet is necessary
    """
    with settings(warn_only=True):
        if run("df -Th | grep %s" % mfsmaster).succeeded:
            return True
        else:
            # print "begin-fabric.state.connections: ", fabric.state.connections
            # print "Host string0:", env.host_string
            if run("test -d %s" % workdir).failed:
                # print "Host string1:", env.host_string
                run("mkdir %s" % workdir)
            # check if log dir exists
            if run("test -d /var/log/mario/").failed:
                run("mkdir /var/log/mario")
            # print "After first run - fabric.state.connections: ", fabric.state.connections
            if run("rpm -qa | grep moosefs-client").failed:
                if run("rpm -qa | grep fuse").failed:
                    if run("yum install fuse fuse-libs -y").failed:
                        abort("Failed to install fuse")
                if run("grep -q -i 'release 6' /etc/redhat-release").succeeded:
                    if put(client6_rpm, workdir).failed:
                        abort("Failed to put MooseFS-client rpm package to ")
                    with cd(workdir):
                        if run("rpm -ivh moosefs-client-3.0.88-1.rhsysv.x86_64.rpm").failed:
                            abort("Failed to install moosefs-client")
                elif run("grep -q -i 'release 7' /etc/redhat-release").succeeded:
                    if put(client7_rpm, workdir).failed:
                        abort("Failed to put MooseFS-client rpm package to ")
                    with cd(workdir):
                        if run("rpm -ivh moosefs-client-3.0.86-1.rhsystemd.x86_64.rpm").failed:
                            abort("Failed to install moosefs-client")
            # deal with firewall on rhel6 or rhel7
            if run("grep -q -i 'release 6' /etc/redhat-release").succeeded:
                if run("service iptables status").succeeded:
                    if run("service iptables stop").failed:
                        abort("Failed to disable iptable")
            elif run("grep -q -i 'release 7' /etc/redhat-release").succeeded:
                if run("systemctl status firewalld.service").succeeded:
                    if run("systemctl stop firewalld.service && systemctl disable firewalld.service").failed:
                        abort("Failed to disable iptable")
            if run("test -d %s" % mountdir).failed:
                run("mkdir %s" % mountdir)
            if run("mfsmount %s -H %s" % (mountdir, mfsmaster)).failed:
                abort("Failed to mount mfs filesystem")
            # after mounting moosefs, copy necessary files to workdir
            with cd(workdir):
                # generate app server config
                run("echo  %s > appconfig" % mario_ip)
                if run("cp %s ." % daemonpy).failed:
                    abort("Failed to copy daemon.py")
                if run("cp %s ." % destroyvmpy).failed:
                    abort("Failed to copy destroy_all_vms.py")
                # check if redis-py installed
                if run("python2.7 -c 'import redis'").failed:
                    if run("cp %s ." % redistar).failed:
                        abort("Failed to copy redis-2.10.5.tar.gz")
                        # decompress and install redis-py
                    if run("tar -xvf redis-2.10.5.tar.gz").failed:
                        abort("Failed to decompress redis-py")
                    with cd("redis-2.10.5"):
                        if run("python2.7 setup.py install").failed:
                            abort("Failed to install redis-py")
                # check if paramiko installed, paramiko must be installed manaually, because its environment is very complex(python2.72.6 install may differs from python2.72.7)
                if run("python2.7 -c 'import paramiko'").failed:
                    abort("Test Server must be installed paramiko!")
                # After install redis-py and paramiko, daenon just run
                if run("python2.7 daemon.py start --ip %s" %host).failed:
                    abort("Falied to start daemon process")
                # check if sysbench exists
                if run("sysbench --version").failed:
                    if run("cp %s /usr/local/src/" % sysbenchtar).failed:
                        abort("Failed to copy sysbench-1.0.1.tar.gz")
                    with cd("/usr/local/src/"):
                        if run("tar -xvf sysbench-1.0.1.tar.gz").failed:
                            abort("Failed to decompress sysbench-1.0.1.tar.gz")
                        if run("yum install -y libtool.x86_64").failed:
                            abort("Faile to install necessary packages for sysbench.")
                        with cd("sysbench-1.0.1"):
                            if run("./autogen.sh").failed:
                                abort("Failed to autogen sysbench")
                            if run("./configure --without-mysql").failed:
                                abort("Failed to configure sysbench")
                            if run("make -j 4").failed:
                                abort("Failed to make sysbench")
                            if run("make install").failed:
                                abort("Failed to make install sysbench")
                # check if iozone exists
                if run("/usr/local/src/iozone3_465/src/current/iozone -v").failed:
                    if run("cp %s /usr/local/src/" % iozonetar).failed:
                        abort("Failed to copy iozone3_465.tar")
                    with cd("/usr/local/src/"):
                        if run("tar -xvf iozone3_465.tar").failed:
                            abort("Failed to decompress iozone3_465.tar")
                        with cd("iozone3_465/src/current/"):
                            if run("make linux-AMD64").failed:
                                abort("Failed to install iozone!")
                if run("cp %s /usr/local/src/" % streamtar).failed:
                    abort("Failed to copy stream.tar")
                with cd("/usr/local/src/"):
                    if run("tar -xvf stream.tar").failed:
                        abort("Failed to decompress stream.tar")
            return True


def prepareTest(app, host, passwd):
    print "In prepareTest .."
    env.passwords['root@%s:22' % (host,)] = passwd
    with app.app_context():
        try:
            db_host = Host.query.filter_by(IP=host).first()
            print "Get a host: ", host
            execute(prepareVM, host, hosts=[host])
            print "prepare finished!"
            db_host.status = "ready"
        except SystemExit:
            db_host.status = "prepare_failed"
        finally:
            db.session.add(db_host)
            db.session.commit()
            disconnect_all()

def clearhost():
    with settings(warn_only=True):
        with cd("%s" % Config.WORK_DIR):
            if run("python2.7 daemon.py status").succeeded:
                # before umount mfs, must stop all the vms, because vm will use backend image on the mfs
                if run("python2.7 destroy_all_vms.py").failed:
                    abort("Before unmouting mfs, can't destroy all the vms")
                run("python2.7 daemon.py stop")
        with cd("/"):
            if run("df -Th | grep %s" % Config.MFS_MASTER).succeeded:
                if run("umount %s" % Config.MFS_MOUNT_POINT).failed:
                    abort("Failed to umount mfs")
            if run("test -d %s" % Config.WORK_DIR).succeeded:
                if run("rm -rf %s" % Config.WORK_DIR).failed:
                    abort("Failed to remove %s" % Config.WORK_DIR)
    return True

def collect_result(app):
    with app.app_context():
        p = conn.pubsub(ignore_subscribe_messages=True)
        print 'redis thread is liestening ... '
        # scan database to subscribe newly added hosts
        hosts_dict = dict((host.id, host.IP) for host in Host.query.all())
        for host in Host.query.all():
            p.subscribe("%s:RESULT" % host.IP)
            # print "subscrube channel %s:RESULT\n" % host.IP
        while True:
            message = p.get_message()
            if message:
                print "recive result: ", message
                message_json = json.loads(message['data'])
                if message_json['type'] == 'cpu':
                    if message_json['success']:
                        print 'starts storing cpu test result ...'
                        result = CPUResult(IP=message_json['IP'], success=message_json['success'], pmresult=message_json['pmresult'],
                        vmresult=message_json['vmresult'], deployTime=message_json['deployTime'])
                    else:
                        print 'starts storing cpu test error information ...'
                        result = CPUResult(IP=message_json['IP'], success=message_json['success'], deployTime=message_json['deployTime'],
                        pmerrorInfo=message_json['pmerrorInfo'] if 'pmerrorInfo' in message_json else None,
                        vmerrorInfo=message_json['vmerrorInfo'] if 'vmerrorInfo' in message_json else None, )
                elif message_json['type'] == 'mem':
                    if message_json['success']:
                        print 'starts storing mem test result ...'
                        result = MemResult(IP=message_json['IP'], success=message_json['success'], pmresult=message_json['pmresult'],
                        vmresult=message_json['vmresult'], deployTime=message_json['deployTime'])
                    else:
                        print 'starts storing mem test error information ...'
                        result = MemResult(IP=message_json['IP'], success=message_json['success'], deployTime=message_json['deployTime'],
                        pmerrorInfo=message_json['pmerrorInfo'] if 'pmerrorInfo' in message_json else None,
                        vmerrorInfo=message_json['vmerrorInfo'] if 'vmerrorInfo' in message_json else None, )
                elif message_json['type'] == 'io':
                    if message_json['success']:
                        print 'starts storing io test result ...'
                        result = IOResult(IP=message_json['IP'], success=message_json['success'], deployTime=message_json['deployTime'],
                                        pmInitialWrite=message_json['pmInitialWrite'], pmRewrite=message_json['pmRewrite'],
                                        pmRead=message_json['pmRead'], pmReRead=message_json['pmReRead'],
                                        vmInitialWrite=message_json['vmInitialWrite'], vmRewrite=message_json['vmRewrite'],
                                        vmRead=message_json['vmRead'], vmReRead=message_json['vmReRead'])
                    else:
                        print 'starts storing io test error information ...'
                        result = IOResult(IP=message_json['IP'], success=message_json['success'], deployTime=message_json['deployTime'],
                        pmerrorInfo=message_json['pmerrorInfo'] if 'pmerrorInfo' in message_json else None,
                        vmerrorInfo=message_json['vmerrorInfo'] if 'vmerrorInfo' in message_json else None, )
                # store the result
                try:
                    db.session.add(result)
                    db.session.commit()
                except IntegrityError:
                    print 'oh~ Failed to store.'
                    db.session.rollback()
            # clear the database session
            db.session.remove()
            hosts_dict_check = dict((host.id, host.IP) for host in Host.query.all())
            # check if there are newly added hosts
            newly_add_hosts = []
            for id in hosts_dict_check:
                if id not in hosts_dict:
                    newly_add_hosts.append(hosts_dict_check[id])
            # check if there are deleted hosts
            deleted_hosts = []
            for id in hosts_dict:
                if id not in hosts_dict_check:
                    deleted_hosts.append(hosts_dict[id])
            # subscribe newly added hosts and unsubscribe deleted hosts
            if newly_add_hosts:
                for host_ip in newly_add_hosts:
                    p.subscribe("%s:RESULT" % host_ip)
            if deleted_hosts:
                for host_ip in deleted_hosts:
                    p.unsubscribe("%s:RESULT" % host_ip)
            hosts_dict = hosts_dict_check


def rmhost(host, passwd):
    env.passwords['root@%s:22' % (host,)] = passwd
    try:
        execute(clearhost, hosts=[host])
    except SystemExit:
        return False
    finally:
        disconnect_all()
    return True


def defineVM(vmnum=1, existvmnum=0, **vmpara):
    """
    VM creation:
        * create qcow2 image based on the base image
        * configure xml for the VM()
        * successfully define VM
    param: VM num to define, VM type(dict)
    """
    if not vmpara:
        vmtype = "standard"
    else:
        vmtype = vmpara['vmtype']
    with settings(warn_only=True):
        with cd(workdir):
            i = 0
            while i < vmnum:
                if run("qemu-img create -f qcow2 -b %s %s-%d.qcow2" % (baseimg, vmtype, existvmnum + i)).succeeded:
                    if run("cp %s %s-%d.xml " % (basexml, vmtype, existvmnum + i)).succeeded:
                        if run("python2.7 domaindefine.py %s-%d.xml %s-%d.qcow2" % (
                        vmtype, existvmnum + i, vmtype, existvmnum + i)).succeeded:
                            i += 1
                        else:
                            break
                    else:
                        break
                else:
                    break

            if i == vmnum:
                return True
            else:
                if run("ls %s-%d.qcow2" % (vmtype, existvmnum + i)).succeeded:  # check the failure image whether exists
                    run("rm -f %s-%d.qcow2" % (vmtype, existvmnum + i))
                if run("ls %s-%d.xml" % (vmtype, existvmnum + i)).succeeded:  # check the failure xml whether exists
                    run("rm -f %s-%d.xml" % (vmtype, existvmnum + i))
                while i > 0:
                    run("rm -f %s-%d.qcow2 %s-%d.xml" % (vmtype, existvmnum + i - 1, vmtype,
                                                         existvmnum + i - 1))  # delete the already created VMs (automicity)
                    --i
                abort("Failed to create %d vm image(s)." % vmnum)



def checkVMnum():
    """
    Check VM nums: return VM num
    """
    with cd(workdir):
        with settings(warn_only=True):
            numStr = run("ls *.xml | wc -l")
            if numStr.failed:
                abort("checkVMnum failed!")
            else:
                # print "type: ", type(int(numStr)), int(numStr)
                print "numStr: ", numStr
                if numStr.startswith('ls'):
                    return 0
                else:
                    return int(numStr)


if __name__ == '__main__':
    """
    try:
        execute(prepareVM, hosts=[host])
        vmnum = execute(checkVMnum, hosts=[host])
        print vmnum[host]
        execute(defineVM, 2, vmnum[host], hosts=[host])
    except SystemExit:
        print "Host[%s] failed to prepare well" % host
    finally:
        disconnect_all()
    """
    print client_rpm
