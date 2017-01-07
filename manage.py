#!/usr/bin/env python
import os
from app import create_app, db, socketio
from app.models import Host
from flask_script import Manager, Shell, Option, Server as _Server
from flask_migrate import Migrate, MigrateCommand
from flask import current_app


app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


class Server(_Server):
    help = description = 'Runs the Socket.IO web server'

    def get_options(self):
        options = (
            Option('-h', '--host',
                   dest='host',
                   default=self.host),

            Option('-p', '--port',
                   dest='port',
                   type=int,
                   default=self.port),

            Option('-d', '--debug',
                   action='store_true',
                   dest='use_debugger',
                   help=('enable the Werkzeug debugger (DO NOT use in '
                         'production code)'),
                   default=self.use_debugger),
            Option('-D', '--no-debug',
                   action='store_false',
                   dest='use_debugger',
                   help='disable the Werkzeug debugger',
                   default=self.use_debugger),

            Option('-r', '--reload',
                   action='store_true',
                   dest='use_reloader',
                   help=('monitor Python files for changes (not 100%% safe '
                         'for production use)'),
                   default=self.use_reloader),
            Option('-R', '--no-reload',
                   action='store_false',
                   dest='use_reloader',
                   help='do not monitor Python files for changes',
                   default=self.use_reloader),
        )
        return options

    def __call__(self, app, host, port, use_debugger, use_reloader):
        # override the default runserver command to start a Socket.IO server
        if use_debugger is None:
            use_debugger = app.debug
            if use_debugger is None:
                use_debugger = True
        if use_reloader is None:
            use_reloader = app.debug
        socketio.run(app,
                     host=host,
                     port=port,
                     debug=use_debugger,
                     use_reloader=use_reloader,
                     **self.server_options)

manager.add_command("runserver", Server())


def make_shell_context():
    return dict(app=app, db=db, Host=Host)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)



"""
manager.command decorator makes it simple to implement custom commands, the name of decorated
function is used as the command name
"""
@manager.command
def test():
    """Run the unit tests"""
    import unittest
    tests = unittest.TestLoader().discover('tests')     # unittest package discovers the tests package
    unittest.TextTestRunner(verbosity=2).run(tests)     # run tests package test cases

"""
@manager.command
def run():
    socketio.run(current_app,
                 host='0.0.0.0',
                 port=5000,
                 use_reloader=False)
"""

if __name__ == '__main__':
    #socketio.run(app)
    manager.run()
