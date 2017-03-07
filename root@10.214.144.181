import xml.etree.ElementTree as ET
import subprocess as sp
from subprocess import CalledProcessError
import random
import time

def get_ip_from_mac(mac):
	return sp.check_output("virsh net-dhcp-leases default %(mac)s | grep %(mac)s | awk '{print $5}'" % {'mac': mac}, shell=True).strip()[:-3]
 
cpu_cores = int(sp.check_output("cat /proc/cpuinfo | grep 'processor' | wc -l ", shell=True))
vm_mem =  float(sp.check_output("free -mh | grep Mem | awk '{print $2}'", shell=True).strip('G\n'))
mac = [ 0x52, 0x54, 0x00,
       random.randint(0x00, 0x7f),
       random.randint(0x00, 0xff),
       random.randint(0x00, 0xff) ]
mac_addr = ':'.join(map(lambda x: "%02x" % x, mac))
print type(mac_addr), mac_addr

# create qcow2 format incremental image
sp.call("qemu-img create -f qcow2 -b /mnt/mfs/sl6-bk.img /var/lib/libvirt/images/vm-cpu.qcow2", shell=True)

# write config file
tree = ET.ElementTree(file="/mnt/mfs/base.xml")
tree.find('name').text = "cpu-vm"
tree.find('memory').text = str(vm_mem / 2)
tree.find('currentMemory').text = str(vm_mem / 2)
tree.find('vcpu').text = str(cpu_cores)
tree.find('devices/interface[@type="network"]/mac').attrib['address'] = mac_addr
tree.find('devices/disk[@device="disk"]/source').attrib['file'] = "/var/lib/libvirt/images/vm-cpu.qcow2"
tree.write('/home/buwei/cpu-vm.xml')

try:
    sp.check_call("virsh create /home/buwei/cpu-vm1.xml", shell=True)
except CalledProcessError as cpe:
    print cpe
time.sleep(30)
ip = get_ip_from_mac(mac_addr)
while not ip:
	time.sleep(5)
	ip = get_ip_from_mac(mac_addr)
print ip

print#print get_ip_from_mac(mac_addr)
