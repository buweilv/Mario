from flask import render_template, redirect, url_for, request, jsonify, g, current_app
from .. import  db
from ..models import Host
from . import main
from ..vmutils import prepareTest
import paramiko
from paramiko.client import SSHClient
from sqlalchemy.exc import IntegrityError
from threading import Thread
import socket


@main.route('/', methods=['GET', 'POST'])
def index():
    all_hosts = Host.query.all()
    return render_template('dashboard.html', hosts=all_hosts)


@main.route('/_del_hosts', methods=['POST'])
def del_hosts():
    print request.form.items()  # debug info: print the to be deleted hosts
    for item in request.form.items():
        print "item is", item
        dl_host = Host.query.filter_by(id=item[1]).first()
        db.session.delete(dl_host)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'ok': False})
    return jsonify({'ok': True})


@main.route('/_add_host', methods=['POST'])
def add_host():
    ip = request.form.get('ip')
    passwd = request.form.get('passwd')
    print ip, passwd # debug info: print the host and passwd info
    if ip and passwd:
        host = Host.query.filter_by(IP=ip).first()
        if not host:
            """
            validate the IP and password is correct
            """
            client = SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                client.connect(username="root", password=passwd, hostname=ip)
                ad_host = Host(IP=ip, password=passwd, status="managed")
                db.session.add(ad_host)
                db.session.commit()
            except socket.gaierror:
                return jsonify({'input_ok': 'invalid hostname'})
            except paramiko.AuthenticationException:
                return jsonify({'input_ok': 'auth failed'})
            except paramiko.ssh_exception.NoValidConnectionsError:
                return jsonify({'input_ok': 'check the machine if ready'})
            except IntegrityError:
                db.session.rollback()
                return jsonify({'input_ok': 'database failed'})
            app = current_app._get_current_object()
            thr = Thread(target=prepareTest, args=[app,  ip, passwd])
            thr.start()
            sd_host = Host.query.filter_by(IP=ip).first()
            print "id, IP", sd_host.id, sd_host.IP
            return jsonify({'input_ok': 'host added success',
                            'id': sd_host.id,
                            'IP': sd_host.IP,
                            'status': sd_host.status})
        else:
            return jsonify({'input_ok': 'host already added'})
    else:
        return jsonify({'input_ok': 'empty field'})

