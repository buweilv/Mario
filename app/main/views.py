from flask import render_template, flash, redirect, url_for, request, jsonify
from .. import  db
from ..models import Host
from . import main
from .forms import HostForm
import paramiko
from paramiko.client import SSHClient
from sqlalchemy.exc import IntegrityError


@main.route('/', methods=['GET', 'POST'])
def index():
    host_form = HostForm()
    all_hosts = Host.query.all()
    if host_form.validate_on_submit():
        client = SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(username="root", password=host_form.passwd.data, hostname=host_form.IP.data)
            flash('Authentication Success!', 'info')
            host = Host.query.filter_by(IP=host_form.IP.data).first()
            if host is None:
                host = Host(IP=host_form.IP.data, password=host_form.passwd.data, status="managed")
                db.session.add(host)
            else:
                flash('This Host has already added!', 'info')
            return redirect(url_for("main.index"))
        except paramiko.AuthenticationException:
            flash('Authentication Failed, Please Check Your Host Information!', 'error')
            return redirect(url_for('main.index'))
    return render_template('dashboard.html', form=host_form, hosts=all_hosts)


@main.route('/_del_hosts', methods=['post'])
def del_host():
    print request.form.items()
    for item in request.form.items():
        dl_host = Host.query.filter_by(id=item[1]).first()
        db.session.delete(dl_host)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'ok': False})
    return jsonify({'ok': True})