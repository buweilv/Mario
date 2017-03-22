import subprocess as sp

vm_ids = sp.check_output("virsh list | grep running | grep -e '-vm' | awk '{print $1}'", shell=True).split("\n")
vm_ids.pop()
print vm_ids
for vm_id in vm_ids:
	sp.call("virsh destroy %s" % vm_id, shell=True)
