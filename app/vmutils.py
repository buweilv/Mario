import fabric
import os
from fabric.api import execute, settings, run, abort, put, cd, env
from fabric.network import disconnect_all
from config import Config
from threading import Thread
from flask import g
from . import db
from .models import Host


workdir = Config.WORK_DIR
mountdir = Config.MFS_MOUNT_POINT
mfsmaster = Config.MFS_MASTER
# host = "10.214.144.181"
env.user = "root"
#env.password = "root"
baseimg = mountdir + "centos7-bk.img"
basexml = mountdir + "host-base.xml"
domaindfpy = mountdir + "domaindefine.py"
client_rpm = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir,
                          'tools/moosefs-client-3.0.86-1.rhsystemd.x86_64.rpm'))


def prepareVM():
    """
    prepare for the VM creation:
        * create work dir
        * install mfs client
        * disable iptable
        * create mfsmount dir
        * mount mfs
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
            # print "After first run - fabric.state.connections: ", fabric.state.connections
            if run("rpm -qa | grep moosefs-client").failed:
                if put(client_rpm, workdir).failed:
                    abort("Failed to put MooseFS-client rpm package to ")
                if run("rpm -qa | grep fuse").failed:
                    if run("yum install fuse fuse-libs -y").failed:
                        abort("Failed to install fuse")
                with cd(workdir):
                    if run("rpm -ivh moosefs-client-3.0.86-1.rhsystemd.x86_64.rpm").failed:
                        abort("Failed to install moosefs-client")
            if run("systemctl status firewalld.service").succeeded:
                if run("systemctl stop firewalld.service && systemctl disable firewalld.service").failed:
                    abort("Failed to disable iptable")
            if run("test -d %s" % mountdir).failed:
                run("mkdir %s" % mountdir)
            if run("mfsmount %s -H %s" % (mountdir, mfsmaster)).failed:
                abort("Failed to mount mfs filesystem")
            # copy necessary files to workdir: domaindefine.py
            with cd(workdir):
                if run("cp %s ." % domaindfpy).failed:
                    abort("Failed to copy domaindefine.py")
            return True

def prepareTest(app, host, passwd):
    from fabric.api import env
    env.passwords['root@%s:22'%(host,)] = passwd
    with app.app_context():
        try:
            db_host = Host.query.filter_by(IP=host).first()
            execute(prepareVM, hosts=[host])
            db_host.status = "ready"
        except SystemExit:
            db_host.status = "prepare_failed"
        finally:
            db.session.add(db_host)
            db.session.commit()
            disconnect_all()


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
                        if run("python domaindefine.py %s-%d.xml %s-%d.qcow2" % (
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


def createVM():
    """
    VM configuration:
        * Dynamically allocate IP to the VM(multiple VMs, if other PM has VM allocated, the IP pool should be shared)
        * successfully start vm, and check if it can ping to the host
    param: VM num to start
    """


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
