from flask import render_template, redirect, url_for, request, jsonify, g, current_app
from .. import db, socketio, conn
from ..models import Host, CPUResult, MemResult, IOResult
from . import main
from ..vmutils import prepareTest, rmhost, collect_result
from flask_socketio import emit, disconnect
from paramiko.client import SSHClient
from sqlalchemy.exc import IntegrityError
from threading import Thread
import paramiko
import socket
import json
import datetime



thread = None
redis_thread = None

def background_thread(app=None):
    """
    if host status changed, send event and changed host status to the client
    """
    with app.app_context():
        while True:
            # update host info interval
            socketio.sleep(app.config['HOST_UPDATE_INTERVAL'])
            # socketio.sleep(5)
            """
            # test websocket connection
            socketio.emit('my_response',
                        {'data': 'Server connected'},
                        namespace='/hostinfo')
            """
            all_hosts = dict([(host.id, host.status) for host in Host.query.all()])
            #print all_hosts
            #all_hosts['test'] = 'test'
            socketio.emit('update_host', all_hosts, namespace='/hostinfo')
            db.session.remove()



@main.route('/', methods=['GET', 'POST'])
def index():
    all_hosts = Host.query.all()
    # return render_template('dashboard.html', hosts=all_hosts)
    return render_template('dashboard.html', hosts=all_hosts, async_mode=socketio.async_mode)


@main.route('/_del_hosts', methods=['POST'])
def del_hosts():
    print request.form.items()  # debug info: print the to be deleted hosts
    for item in request.form.items():
        print "item is", item
        dl_host = Host.query.filter_by(id=item[1]).first()
        if rmhost(dl_host.IP, dl_host.password):
            db.session.delete(dl_host)
        else:
            dl_host.status = "remove_failed"
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'ok': False})
    return jsonify({'ok': True})


@main.route('/_del_results', methods=['POST'])
def del_results():
    print request.form.items()  # debug info: print the to be deleted hosts
    for item in request.form.items():
        print "item is", item
        type, id = item[1].split('_')
        if type == 'cpu':
            dl_result = CPUResult.query.filter_by(id=int(id)).first()
        elif type == 'mem':
            dl_result = MemResult.query.filter_by(id=int(id)).first()
        if type == 'io':
            dl_result = IOResult.query.filter_by(id=int(id)).first()
        db.session.delete(dl_result)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'ok': False})
    return jsonify({'ok': True})
    

@main.route('/_cpu_test',methods=['POST'])
def cpu_test():
    print request.form.items() # debug info: print the cpu test hosts
    status_dict = {}
    """
    status:
    'more than one' (listening)
    'no one' (listening)
    'success' (just one client listening)
    """
    for item in request.form.items():
        print "item is", item
        test_host = Host.query.filter_by(id=item[1]).first().IP
        # generate deploy time, and send deploy info
        now = datetime.datetime.now()
        deploytime = now.strftime("%Y-%m-%d-%H%M%S")
        deploy_json = {
            'type': 'cpu',
            'time': deploytime
        }
        deploy_str = json.dumps(deploy_json)
        recv_num = conn.publish(test_host, deploy_str)
        if recv_num > 1:
            status_dict[test_host] = 'more than one'
            # return jsonify({'deploy_ok': 'more than one', 'IP': test_host})
        elif recv_num == 0:
            status_dict[test_host] = 'no one'
            # return jsonify({'deploy_ok': 'no server accept', 'IP': test_host})
        else:
            status_dict[test_host] = 'success'
    return jsonify(status_dict)


@main.route('/_mem_test',methods=['POST'])
def mem_test():
    print request.form.items() # debug info: print the cpu test hosts
    status_dict = {}
    """
    status:
    'more than one' (listening)
    'no one' (listening)
    'success' (just one client listening)
    """
    for item in request.form.items():
        print "item is", item
        test_host = Host.query.filter_by(id=item[1]).first().IP
        # generate deploy time, and send deploy info
        now = datetime.datetime.now()
        deploytime = now.strftime("%Y-%m-%d-%H%M%S")
        deploy_json = {
            'type': 'mem',
            'time': deploytime
        }
        deploy_str = json.dumps(deploy_json)
        recv_num = conn.publish(test_host, deploy_str)
        if recv_num > 1:
            status_dict[test_host] = 'more than one'
            # return jsonify({'deploy_ok': 'more than one', 'IP': test_host})
        elif recv_num == 0:
            status_dict[test_host] = 'no one'
            # return jsonify({'deploy_ok': 'no server accept', 'IP': test_host})
        else:
            status_dict[test_host] = 'success'
    return jsonify(status_dict)


@main.route('/_io_test',methods=['POST'])
def io_test():
    print request.form.items() # debug info: print the cpu test hosts
    status_dict = {}
    """
    status:
    'more than one' (listening)
    'no one' (listening)
    'success' (just one client listening)
    """
    for item in request.form.items():
        print "item is", item
        test_host = Host.query.filter_by(id=item[1]).first().IP
        # generate deploy time, and send deploy info
        now = datetime.datetime.now()
        deploytime = now.strftime("%Y-%m-%d-%H%M%S")
        deploy_json = {
            'type': 'io',
            'time': deploytime
        }
        deploy_str = json.dumps(deploy_json)
        recv_num = conn.publish(test_host, deploy_str)
        if recv_num > 1:
            status_dict[test_host] = 'more than one'
            # return jsonify({'deploy_ok': 'more than one', 'IP': test_host})
        elif recv_num == 0:
            status_dict[test_host] = 'no one'
            # return jsonify({'deploy_ok': 'no server accept', 'IP': test_host})
        else:
            status_dict[test_host] = 'success'
    return jsonify(status_dict)


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
            # print "id, IP", sd_host.id, sd_host.IP
            return jsonify({'input_ok': 'host added success',
                            'id': sd_host.id,
                            'IP': sd_host.IP,
                            'status': sd_host.status})
        else:
            return jsonify({'input_ok': 'host already added'})
    else:
        return jsonify({'input_ok': 'empty field'})

@main.route('/_get_cpu_result')
def get_cpu_result():
    id = request.args.get('id')
    print id
    cpu_result = CPUResult.query.filter_by(id=id).first()
    if cpu_result.success:
        return jsonify({'type': "cpu",
                        'deployTime': cpu_result.deployTime,
                        'IP': cpu_result.IP,
                        'pmresult': cpu_result.pmresult,
                        'vmresult': cpu_result.vmresult})
    else:
        return jsonify({'type': "cpu",
                        'deployTime': cpu_result.deployTime,
                        'IP': cpu_result.IP,
                        'pmerrorInfo': cpu_result.pmerrorInfo,
                        'vmerrorInfo': cpu_result.vmerrorInfo})

@main.route('/_get_mem_result')
def get_mem_result():
    id = request.args.get('id')
    mem_result = MemResult.query.filter_by(id=id).first()
    if mem_result.success:
        return jsonify({'type': "mem",
                        'deployTime': mem_result.deployTime,
                        'IP': mem_result.IP,
                        'pmresult': mem_result.pmresult,
                        'vmresult': mem_result.vmresult})
    else:
        return jsonify({'type': "mem",
                        'deployTime': mem_result.deployTime,
                        'IP': mem_result.IP,
                        'pmerrorInfo': mem_result.pmerrorInfo,
                        'vmerrorInfo': mem_result.vmerrorInfo})


@main.route('/_get_io_result')
def get_io_result():
    id = request.args.get('id')
    io_result = IOResult.query.filter_by(id=id).first()
    if io_result.success:
        return jsonify({'type': "io",
                        'deployTime': io_result.deployTime,
                        'IP': io_result.IP,
                        'pmInitialWrite': io_result.pmInitialWrite,
                        'pmRewrite': io_result.pmRewrite,
                        'pmRead': io_result.pmRead,
                        'pmReRead': io_result.pmReRead,
                        'vmInitialWrite': io_result.vmInitialWrite,
                        'vmRewrite': io_result.vmRewrite,
                        'vmRead': io_result.vmRead,
                        'vmReRead': io_result.vmReRead})
    else:
        return jsonify({'type': "io",
                        'deployTime': io_result.deployTime,
                        'IP': io_result.IP,
                        'pmerrorInfo': io_result.pmerrorInfo,
                        'vmerrorInfo': io_result.vmerrorInfo})


@main.route('/_view_results')
def view_results():
    results = []
    cpu_results = CPUResult.query.all()
    mem_results = MemResult.query.all()
    io_results = IOResult.query.all()
    results.extend(cpu_results)
    results.extend(mem_results)
    results.extend(io_results)
    return render_template('result.html', results=results, async_mode=socketio.async_mode)


@socketio.on('connect', namespace='/hostinfo')
def on_connect():
    global thread
    global redis_thread
    print 'connected!'
    if thread is None:
        app = current_app._get_current_object()
        thread = socketio.start_background_task(target=background_thread, app=app)
        print 'create host status thread to push newest host info to clients ...'
    if redis_thread is None:
        app = current_app._get_current_object()
        redis_thread = Thread(target=collect_result, args=(app,))
        redis_thread.start()
        print 'create redis thread listening for result info ...'
    emit('my_response', {'data': 'conncted'})


@socketio.on('disconnect', namespace='/hostinfo')
def on_disconnect():
    print 'Client disconnected...', request.sid


@socketio.on('my_ping', namespace="/hostinfo")
def ping_pong():
    emit('my_pong')


