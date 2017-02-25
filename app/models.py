# coding=utf-8
from . import db


class Host(db.Model):
    __tablename__ = 'hosts'
    id = db.Column(db.Integer, primary_key=True)
    #    username = db.Column(db.String(64))
    IP = db.Column(db.String(64), unique=True)
    password = db.Column(db.String(64))
    status = db.Column(db.String(64))

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed, randint
        import forgery_py

        status = ['managed', 'disconnect', 'ready']
        """
            managed: ip 密码验证通过
            ready: mangaed -> ready状态转换存在一个对待测主机进行配置的过程,ready表示这个过程已经完成，进入待测试状态
            disconnect: 如果待测主机因为某些原因断开连接，就变成这个状态。默认设置比如1min钟检查连接是否断开，也可以提供一个按钮让用户检测
        """
        seed()
        for i in range(count):
            host = Host(IP=forgery_py.internet.ip_v4(),
                        password=forgery_py.lorem_ipsum.word(),
                        status=status[randint(0, 2)])
            db.session.add(host)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def __repr__(self):
        return '<Host id: %r, Host IP: %r; Host status: %r>' % (self.id, self.IP, self.status)

class CPUResult(db.Model):
    __tablename__ = "cpuresults"
    # result: sysbench run total time (s) 
    id = db.Column(db.Integer, primary_key=True)
    IP = db.Column(db.String(64))
    deployTime = db.Column(db.String(64))
    success = db.Column(db.Boolean)
    pmresult = db.Column(db.Float, default=0)
    pmerorInfo = db.Column(db.Text, nullable=True)
    vmresult = db.Column(db.Float, default=0)
    vmerorInfo = db.Column(db.Text, nullable=True)

    def __repr__(self):
        error_message = ""
        if self.success:
            return 'Host %s run cpu benchmark on pm costs %fs, on vm costs %fs' % (self.IP, self.pmresult, self.vmresult)
        else:
            if pmerorInfo:
                error_message += 'Host %s run cpu benchmark on pm get error:\n %s \n' % (self.IP, self.pmerrorinfo)
            if vmerorInfo:
                error_message += 'Host %s run cpu benchmark on vm get error:\n %s \n' % (self.IP, self.vmerrorinfo)
            return error_message


class MemResult(db.Model):
    __tablename__ = "memresults"
    # result: Traid throughput 10 times average (MB/s)
    id = db.Column(db.Integer, primary_key=True)
    IP = db.Column(db.String(64))
    deployTime = db.Column(db.String(64))
    success = db.Column(db.Boolean)
    pmresult = db.Column(db.Float, default=0)
    pmerorInfo = db.Column(db.Text, nullable=True)
    vmresult = db.Column(db.Float, default=0)
    vmerorInfo = db.Column(db.Text, nullable=True)

    def __repr__(self):
        error_message = ""
        if self.success:
            return 'Host %s run mem benchmark on pm throughput reach %fMB/s, on vm throughput reach %fMB/s' % (self.IP, self.pmresult, self.vmresult)
        else:
            if pmerorInfo:
                error_message += 'Host %s run mem benchmark on pm get error:\n %s \n' % (self.IP, self.pmerrorinfo)
            if vmerorInfo:
                error_message += 'Host %s run mem benchmark on vm get error:\n %s \n' % (self.IP, self.vmerrorinfo)
            return error_message


class IOResult(db.Model):
    __tablename__ = "ioresults"
    # result: Initial write, Rewrite, read, reread mode speed (kb/s)
    id = db.Column(db.Integer, primary_key=True)
    IP = db.Column(db.String(64))
    deployTime = db.Column(db.String(64))
    success = db.Column(db.Boolean)
    pmInitialWrite = db.Column(db.Float, default=0)
    pmRewrite = db.Column(db.Float, default=0)
    pmRead = db.Column(db.Float, default=0)
    pmReRead = db.Column(db.Float, default=0)
    pmerorInfo = db.Column(db.Text, nullable=True)
    vmInitialWrite = db.Column(db.Float, default=0)
    vmRewrite = db.Column(db.Float, default=0)
    vmRead = db.Column(db.Float, default=0)
    vmReRead = db.Column(db.Float, default=0)
    vmerorInfo = db.Column(db.Text, nullable=True)

    def __repr__(self):
        error_message = ""
        if self.success:
            return 'Host %s run io benchmark on pm read speed reach %fkb/s, on vm read speed reach %fkb/s' % (self.IP, self.pmRead, self.vmRead)
        else:
            if pmerorInfo:
                error_message += 'Host %s run mem benchmark on pm get error:\n %s \n' % (self.IP, self.pmerrorinfo)
            if vmerorInfo:
                error_message += 'Host %s run mem benchmark on vm get error:\n %s \n' % (self.IP, self.vmerrorinfo)
            return error_message
