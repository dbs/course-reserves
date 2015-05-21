#!/usr/bin/env python

from flask import Flask, abort, request, render_template, \
                    make_response, g
from flask_babelex import Babel
from os.path import abspath, dirname
from conf import ConfigFile
import sys
import psycopg2
import StringIO

app = Flask(__name__)
app.root_path = abspath(dirname(__file__))
babel = Babel(app)

c = ConfigFile('config.ini')
opt = {}
opt = c.getsection('Reserves')

if __name__ == '__main__':
    app.run(debug=opt['DEBUG'], host=opt['HOST'], port=opt['PORT'])
