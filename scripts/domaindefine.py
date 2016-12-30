#!/usr/bin/python
# -*- coding: utf-8 -*-


import xml.etree.ElementTree as ET
import argparse
import uuid
import random
import os

parser = argparse.ArgumentParser(usage='./%(prog)s(python %(prog)s) [options]',
                                 description="""
                                 This script is used to define the specified vm template to an available domain.
                                 You don't have to specify uuid, domain name and mac address, every time you use
                                 this script, you will get new available ones. The domain name will default be the
                                 same as config file name(without suffix). But you should specify config filename
                                 and vm image file location, they are necessary. Other paramaters are optional.
                                 """)

parser.add_argument("config", help="the xml config filename")
parser.add_argument("image", help="the vm image filename")
parser.add_argument("-d", "--domain", help="domain name default same as config filename(without suffix)")
args = parser.parse_args()

if args.domain:
    domain_name = args.domain
else:
    if '/' in args.config:
        tmp = args.config.split('/')
        domain_name = tmp[len(tmp)-1].split('.')[0]
    else:
        domain_name = args.config.split('.')[0]
mac = [ 0x00, 0x16, 0x3e,
       random.randint(0x00, 0x7f),
       random.randint(0x00, 0xff),
       random.randint(0x00, 0xff) ]
macaddr = ':'.join(map(lambda x: "%02x" % x, mac))
image_ap = os.path.split(os.path.realpath(__file__))[0] #definedomain.py current dir

#print image_ap
#print "macaddr: ", macaddr
#print "domain name:", domain_name

tree = ET.ElementTree(file=args.config)
#for elem in tree.iter():
#    print elem.tag, elem.attrib
tree.find('name').text = domain_name
tree.find('uuid').text = str(uuid.uuid1())
tree.find('devices/interface[@type="bridge"]/mac').attrib['address'] = macaddr
tree.find('devices/disk[@device="disk"]/source').attrib['file'] = args.image if args.image.startswith('/') else image_ap + '/' + args.image
#print tree.find('devices/disk[@device="disk"]/source').attrib['file']
tree.write(args.config)
