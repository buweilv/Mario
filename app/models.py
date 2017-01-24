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
        return '<Host IP: %r; Host status: %r>' % (self.IP, self.status)
