#!/usr/bin/env python

from flask import Flask, abort, request, render_template, \
                    make_response, g
from flask_login import LoginManager, login_required, current_user, \
                    login_user, logout_user
from flask_babelex import Babel
from os.path import abspath, dirname
from optparse import OptionParser
from conf import ConfigFile
import sys
import ldap
import psycopg2
import database
import StringIO

app = Flask(__name__)
app.root_path = abspath(dirname(__file__))
babel = Babel(app)

c = ConfigFile('config.ini')
opt = {}
opt = c.getsection('Reserves')

parser = OptionParser()
parser.add_option('-d', '--debug', dest='DEBUG', action='store_true',
            help='Provides debug output when unhandled exceptions occur.')
parser.add_option('-v', '--verbose', dest='VERBOSE', action='store_true',
            help='Provides verbose output for what is being done.')
cmd_opt, junk = parser.parse_args()

opt['DEBUG']  = cmd_opt.DEBUG
opt['VERBOSE'] = cmd_opt.VERBOSE

@app.route(opt['APP_ROOT'], methods=['GET','POST'])
def visit_root():
    return render_template('blank.html', data=database.get_reserves()), 200

if __name__ == '__main__':
    app.run(debug=opt['DEBUG'], host=opt['HOST'], port=opt['PORT'])
