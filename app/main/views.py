from flask import render_template, flash, redirect, url_for
from .. import  db
from ..models import Host
from . import main
from .forms import HostForm
import paramiko
from paramiko.client import SSHClient


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

