#!/usr/bin/env python
import os
from app import create_app, db
from app.models import Host
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


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


if __name__ == '__main__':
    manager.run()
